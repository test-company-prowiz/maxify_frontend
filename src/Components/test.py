import sqlite3
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List

from prompt_templates import get_full_system_prompt

DB_FILE = "app_settings.db"

logger = logging.getLogger(__name__)

# ---------------- CACHE ----------------
_settings_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 60


# --------------------------------------------------
# DB CONNECTION
# --------------------------------------------------

def _get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # ✅ WAL MODE
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


# --------------------------------------------------
# MIGRATION HELPERS
# --------------------------------------------------
# All migrations run inside init_db(). Each one is idempotent —
# detects whether it has already run, and is a no-op on subsequent
# startups.

def _table_columns(cursor, table_name: str) -> List[str]:
    """Return the column names of a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _migrate_documented_files_add_branch(cursor):
    """
    Phase 1 migration: add `branch` column to documented_files
    and rebuild the UNIQUE constraint to include it.

    Old schema: UNIQUE(repo_name, file_path)
    New schema: UNIQUE(repo_name, branch, file_path)

    SQLite can't change a UNIQUE constraint in place, so we
    rename the old table, create the new one, copy rows over
    with branch='main' defaulted, then drop the old.

    Idempotent: if the new schema is already in place, returns
    immediately without touching data.
    """
    columns = _table_columns(cursor, "documented_files")

    # If table doesn't exist yet, nothing to migrate
    if not columns:
        return

    # If branch column already exists, migration already happened
    if "branch" in columns:
        return

    logger.info(
        "Migrating documented_files table: adding 'branch' column "
        "and updating UNIQUE constraint"
    )

    # Rename old table out of the way
    cursor.execute("ALTER TABLE documented_files RENAME TO documented_files_old")

    # Create new table with branch column + new unique constraint
    cursor.execute("""
        CREATE TABLE documented_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT NOT NULL,
            branch TEXT NOT NULL DEFAULT 'main',
            file_path TEXT NOT NULL,
            blob_sha TEXT NOT NULL,
            documented_at TEXT,
            UNIQUE(repo_name, branch, file_path)
        )
    """)

    # Backfill from old table with branch='main' defaulted
    # (per mentor's choice — slight imperfection for repos whose
    # default branch isn't 'main', but they'll re-document once
    # and self-correct from there)
    cursor.execute("""
        INSERT INTO documented_files
            (repo_name, branch, file_path, blob_sha, documented_at)
        SELECT
            repo_name, 'main', file_path, blob_sha, documented_at
        FROM documented_files_old
    """)

    # Drop the old table
    cursor.execute("DROP TABLE documented_files_old")

    logger.info("documented_files migration complete")


def _migrate_job_queue_add_branch_columns(cursor):
    """
    Phase 1 migration: add `branch` and `force_regenerate` columns
    to job_queue. These are simple ALTER TABLE ADD COLUMN calls
    since there's no constraint change involved.

    Idempotent: detects existing columns and skips ALTERs.
    """
    columns = _table_columns(cursor, "job_queue")

    if not columns:
        return

    if "branch" not in columns:
        cursor.execute(
            "ALTER TABLE job_queue ADD COLUMN branch TEXT DEFAULT 'main'"
        )
        logger.info("Added 'branch' column to job_queue")

    if "force_regenerate" not in columns:
        cursor.execute(
            "ALTER TABLE job_queue ADD COLUMN force_regenerate INTEGER DEFAULT 0"
        )
        logger.info("Added 'force_regenerate' column to job_queue")


# --------------------------------------------------
# INIT DB
# --------------------------------------------------

def init_db():
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            github_org TEXT,
            github_token TEXT,
            gemini_api_key TEXT,
            webhook_secret TEXT,
            prompt_template TEXT,
            last_updated TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_snapshot TEXT,
            updated_at TEXT,
            version_name TEXT,
            version_description TEXT
        )
    """)

    # Legacy column add (kept from previous migration)
    cursor.execute("PRAGMA table_info(settings_versions)")
    columns = [col[1] for col in cursor.fetchall()]

    if "is_deleted" not in columns:
        cursor.execute(
            "ALTER TABLE settings_versions ADD COLUMN is_deleted INTEGER DEFAULT 0"
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repository_executions (
            repo_name TEXT PRIMARY KEY,
            status TEXT,
            started_at INTEGER,
            completed_at INTEGER,
            duration REAL,
            error_type TEXT,
            error_message TEXT,
            total_runs INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            name TEXT PRIMARY KEY,
            description TEXT,
            default_branch TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT,
            selected_files TEXT,
            retry_failed INTEGER,
            user_prompt TEXT,
            status TEXT DEFAULT 'pending',
            created_at INTEGER,
            branch TEXT DEFAULT 'main',
            force_regenerate INTEGER DEFAULT 0
        )
    """)

    # ✅ documented_files — branch-aware schema (Phase 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documented_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT NOT NULL,
            branch TEXT NOT NULL DEFAULT 'main',
            file_path TEXT NOT NULL,
            blob_sha TEXT NOT NULL,
            documented_at TEXT,
            UNIQUE(repo_name, branch, file_path)
        )
    """)

    # ✅ doc_blobs — cross-branch dedup cache (Phase 3)
    # Keyed by GitHub's blob SHA, which is content-addressable —
    # two files with the same blob SHA have identical content,
    # so the generated doc is reusable across branches and even
    # across repos. Storing the raw Gemini output WITHOUT the
    # metadata header (header is branch-specific and rebuilt
    # fresh each time).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doc_blobs (
            blob_sha TEXT PRIMARY KEY,
            raw_content TEXT NOT NULL,
            generated_at TEXT
        )
    """)

    # ✅ MIGRATIONS for existing installs (idempotent)
    _migrate_documented_files_add_branch(cursor)
    _migrate_job_queue_add_branch_columns(cursor)

    conn.commit()
    conn.close()


# --------------------------------------------------
# SELF HEALING
# --------------------------------------------------

def reset_stuck_jobs():
    """
    Reset ALL in_progress jobs back to pending.
    Used at server startup — any in_progress job after restart is a zombie.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE job_queue
        SET status = 'pending'
        WHERE status = 'in_progress'
    """)

    conn.commit()
    conn.close()


def reset_stale_jobs(threshold_minutes: int = 60) -> int:
    """
    Reset in_progress jobs that have been stuck longer than threshold.
    Used by periodic background cleanup (safer than reset_stuck_jobs
    because it won't kill healthy long-running jobs).

    Returns number of jobs reset.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    threshold_seconds = threshold_minutes * 60
    cutoff_timestamp = int(time.time()) - threshold_seconds

    cursor.execute("""
        UPDATE job_queue
        SET status = 'pending'
        WHERE status = 'in_progress'
        AND created_at < ?
    """, (cutoff_timestamp,))

    reset_count = cursor.rowcount

    conn.commit()
    conn.close()

    return reset_count


def reset_stale_repository_executions(
    threshold_minutes: int = 60,
    startup: bool = False
) -> int:
    """
    Mark stuck repository_executions as failed.

    - At startup (startup=True): mark ALL in_progress as failed (no threshold)
      because any in_progress row after restart is a zombie.
    - During runtime (startup=False): only mark rows older than threshold.

    Returns number of rows marked as failed.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    if startup:
        cursor.execute("""
            UPDATE repository_executions
            SET
                status = 'failed',
                error_type = 'SERVER_RESTART',
                error_message = 'Server restarted while job was in progress'
            WHERE status = 'in_progress'
        """)
    else:
        threshold_seconds = threshold_minutes * 60
        cutoff_timestamp = int(time.time()) - threshold_seconds

        cursor.execute("""
            UPDATE repository_executions
            SET
                status = 'failed',
                error_type = 'STALE_JOB',
                error_message = ?
            WHERE status = 'in_progress'
            AND started_at < ?
        """, (
            f"Job exceeded {threshold_minutes} minute timeout",
            cutoff_timestamp
        ))

    reset_count = cursor.rowcount

    conn.commit()
    conn.close()

    return reset_count


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

def get_settings() -> Optional[Dict]:

    now = time.time()

    if (
        _settings_cache["data"]
        and now - _settings_cache["timestamp"] < CACHE_TTL
    ):
        return _settings_cache["data"]

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM settings WHERE id = 1")
    row = cursor.fetchone()

    data = dict(row) if row else {}

    if not data.get("prompt_template"):
        data["prompt_template"] = get_full_system_prompt()

    cursor.execute("""
        SELECT config_snapshot, version_name, version_description
        FROM settings_versions
        WHERE is_deleted = 0
        ORDER BY id DESC
    """)

    versions = cursor.fetchall()

    def normalize(d):
        return {
            "github_org": d.get("github_org") or "",
            "github_token": d.get("github_token") or "",
            "gemini_api_key": d.get("gemini_api_key") or "",
            "webhook_secret": d.get("webhook_secret") or "",
            "prompt_template": d.get("prompt_template") or "",
        }

    current_clean = normalize(data)

    for v in versions:
        snapshot = normalize(json.loads(v["config_snapshot"]))

        if snapshot == current_clean:
            data["version_name"] = v["version_name"]
            data["version_description"] = v["version_description"]
            break

    conn.close()

    _settings_cache["data"] = data
    _settings_cache["timestamp"] = now

    return data


# --------------------------------------------------
# SAVE SETTINGS
# --------------------------------------------------

def save_settings(data: Dict):

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM settings WHERE id = 1")
    current_row = cursor.fetchone()

    current = dict(current_row) if current_row else {}

    merged = {
        "github_org": data.get("github_org") or current.get("github_org"),
        "github_token": data.get("github_token") or current.get("github_token"),
        "gemini_api_key": data.get("gemini_api_key") or current.get("gemini_api_key"),
        "webhook_secret": data.get("webhook_secret") or current.get("webhook_secret"),
        "prompt_template": (
            data.get("prompt_template")
            if data.get("prompt_template") is not None
            else current.get("prompt_template")
        ),
    }

    def normalize(d):
        return {
            "github_org": d.get("github_org") or "",
            "github_token": d.get("github_token") or "",
            "gemini_api_key": d.get("gemini_api_key") or "",
            "webhook_secret": d.get("webhook_secret") or "",
            "prompt_template": d.get("prompt_template") or "",
        }

    if normalize(current) == normalize(merged):
        conn.close()
        return {"message": "No changes detected"}

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM settings_versions
        WHERE is_deleted = 0
    """)

    count = cursor.fetchone()["count"]

    version_name = data.get("version_name") or f"Version {count + 1}"

    cursor.execute("""
        SELECT 1
        FROM settings_versions
        WHERE version_name = ?
        AND is_deleted = 0
    """, (version_name,))

    if cursor.fetchone():
        conn.close()
        raise Exception("Version name already exists")

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO settings_versions (
            config_snapshot,
            updated_at,
            version_name,
            version_description
        )
        VALUES (?, ?, ?, ?)
    """, (
        json.dumps(merged),
        now,
        version_name,
        data.get("version_description") or ""
    ))

    cursor.execute("""
        INSERT OR REPLACE INTO settings (
            id,
            github_org,
            github_token,
            gemini_api_key,
            webhook_secret,
            prompt_template,
            last_updated
        )
        VALUES (1, ?, ?, ?, ?, ?, ?)
    """, (
        merged["github_org"],
        merged["github_token"],
        merged["gemini_api_key"],
        merged["webhook_secret"],
        merged["prompt_template"],
        now
    ))

    conn.commit()
    conn.close()

    _settings_cache["data"] = None


# --------------------------------------------------
# RESTORE VERSION
# --------------------------------------------------

def restore_version(version_id: int):

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT config_snapshot
        FROM settings_versions
        WHERE id = ?
        AND is_deleted = 0
    """, (version_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    snapshot = json.loads(row["config_snapshot"])
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO settings (
            id,
            github_org,
            github_token,
            gemini_api_key,
            webhook_secret,
            prompt_template,
            last_updated
        )
        VALUES (1, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot.get("github_org"),
        snapshot.get("github_token"),
        snapshot.get("gemini_api_key"),
        snapshot.get("webhook_secret"),
        snapshot.get("prompt_template"),
        now
    ))

    conn.commit()
    conn.close()

    _settings_cache["data"] = None

    return snapshot


# --------------------------------------------------
# VERSION HELPERS
# --------------------------------------------------

def get_versions():

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM settings_versions
        WHERE is_deleted = 0
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    versions = []

    for row in rows:
        item = dict(row)

        try:
            snapshot = json.loads(item["config_snapshot"])
        except:
            snapshot = {}

        item["config_snapshot"] = snapshot
        versions.append(item)

    conn.close()

    return versions


def soft_delete_version(version_id: int):

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE settings_versions
        SET is_deleted = 1
        WHERE id = ?
    """, (version_id,))

    conn.commit()
    conn.close()


def update_version_metadata(
    version_id: int,
    version_name: str,
    version_description: str
):

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM settings_versions
        WHERE version_name = ?
        AND id != ?
        AND is_deleted = 0
    """, (
        version_name,
        version_id
    ))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        raise Exception("Version name already exists")

    cursor.execute("""
        UPDATE settings_versions
        SET
            version_name = ?,
            version_description = ?
        WHERE id = ?
    """, (
        version_name,
        version_description,
        version_id
    ))

    conn.commit()
    conn.close()


# --------------------------------------------------
# DOCUMENTED FILE SHA TRACKING
# --------------------------------------------------
# All functions in this section are now BRANCH-SCOPED.
# Same file path on different branches has independent SHA tracking.

def get_documented_sha(
    repo_name: str,
    branch: str,
    file_path: str
):
    """
    Get the documented SHA for a single file on a specific branch.

    Kept for backward compatibility and one-off lookups. For bulk
    processing, prefer get_all_documented_shas() which fetches the
    entire (repo, branch) in one query.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT blob_sha
        FROM documented_files
        WHERE repo_name = ?
        AND branch = ?
        AND file_path = ?
    """, (
        repo_name,
        branch,
        file_path
    ))

    row = cursor.fetchone()

    conn.close()

    return row["blob_sha"] if row else None


def get_all_documented_shas(
    repo_name: str,
    branch: str
) -> Dict[str, str]:
    """
    Bulk-load all documented file SHAs for a (repo, branch) in one query.

    Bug 7 fix + branch awareness: returns a dict mapping
    file_path → blob_sha for files documented on this specific branch.
    Different branches in the same repo have independent SHA caches.

    Returns:
        dict[str, str]: Mapping of file_path → blob_sha. Empty dict
        if this (repo, branch) has no documented files yet.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT file_path, blob_sha
        FROM documented_files
        WHERE repo_name = ?
        AND branch = ?
    """, (repo_name, branch))

    rows = cursor.fetchall()

    conn.close()

    return {row["file_path"]: row["blob_sha"] for row in rows}


def save_documented_file(
    repo_name: str,
    branch: str,
    file_path: str,
    blob_sha: str
):
    """
    Record that a file was documented on a specific branch.

    Upsert keyed by (repo_name, branch, file_path) — so the same
    file path can have independent SHA tracking per branch.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    documented_at = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO documented_files (
            repo_name,
            branch,
            file_path,
            blob_sha,
            documented_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(repo_name, branch, file_path)
        DO UPDATE SET
            blob_sha = excluded.blob_sha,
            documented_at = excluded.documented_at
    """, (
        repo_name,
        branch,
        file_path,
        blob_sha,
        documented_at
    ))

    conn.commit()
    conn.close()


# --------------------------------------------------
# DOC BLOB DEDUP CACHE (Phase 3)
# --------------------------------------------------
# GitHub's blob SHA is content-addressable: two files with the
# same blob SHA have byte-for-byte identical content. So we can
# generate documentation ONCE per unique blob SHA and reuse it
# across every branch (and every repo) that contains that blob.
#
# What's stored: the raw Gemini output WITHOUT the metadata
# header. The header contains the branch-specific URL, which is
# always rebuilt fresh at commit time.
#
# Cache invalidation: blob SHAs change when content changes, so
# stale content is impossible. The only invalidation scenario is
# "prompt template was updated, regenerate all docs" — handled
# by the force_regenerate flag at the engine level (bypasses
# this cache entirely).

def get_doc_blob(blob_sha: str) -> Optional[str]:
    """
    Look up a cached doc body by blob SHA.

    Returns:
        The raw Gemini output for this blob, or None if we haven't
        documented this content before.
    """
    if not blob_sha:
        return None

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT raw_content FROM doc_blobs WHERE blob_sha = ?",
        (blob_sha,)
    )

    row = cursor.fetchone()

    conn.close()

    return row["raw_content"] if row else None


def save_doc_blob(blob_sha: str, raw_content: str):
    """
    Cache the raw Gemini output for a blob SHA.

    Upsert keyed by blob_sha — if Gemini ran twice for the same
    blob (race condition between two workers documenting different
    branches), the later write wins. Both outputs are valid (same
    blob, same content, same prompt → effectively equivalent), so
    last-write-wins is acceptable.
    """
    if not blob_sha or not raw_content:
        return

    conn = _get_connection()
    cursor = conn.cursor()

    generated_at = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO doc_blobs (blob_sha, raw_content, generated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(blob_sha)
        DO UPDATE SET
            raw_content = excluded.raw_content,
            generated_at = excluded.generated_at
    """, (
        blob_sha,
        raw_content,
        generated_at
    ))

    conn.commit()
    conn.close()


# --------------------------------------------------
# JOB QUEUE
# --------------------------------------------------

def enqueue_job(
    repo_name: str,
    branch: str,
    selected_files,
    retry_failed: bool,
    force_regenerate: bool,
    user_prompt
):
    """
    Enqueue a documentation job.

    New parameters:
      branch:           which branch to document
      force_regenerate: if True, bypass SHA cache and re-generate
                        every file (used when prompt template changes
                        but file contents haven't)
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO job_queue (
            repo_name,
            branch,
            selected_files,
            retry_failed,
            force_regenerate,
            user_prompt,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        repo_name,
        branch or 'main',
        json.dumps(selected_files) if selected_files else None,
        int(bool(retry_failed)),
        int(bool(force_regenerate)),
        user_prompt,
        int(time.time())
    ))

    conn.commit()
    conn.close()


def fetch_next_job():
    """
    Atomically claim the next pending job.

    Returns a dict including the new branch and force_regenerate
    fields, in addition to the existing fields. Same atomic-claim
    pattern as before (Bug 3 fix preserved).
    """
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE job_queue
            SET status = 'in_progress'
            WHERE id = (
                SELECT id
                FROM job_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT 1
            )
            RETURNING *
        """)

        row = cursor.fetchone()
        conn.commit()

        result = dict(row) if row else None

    finally:
        conn.close()

    return result


# --------------------------------------------------
# REPOSITORY EXECUTIONS
# --------------------------------------------------

def upsert_repository_execution(repo_name: str, status: str):

    conn = _get_connection()
    cursor = conn.cursor()

    started_at = int(time.time())

    cursor.execute("""
        INSERT INTO repository_executions (
            repo_name,
            status,
            started_at,
            total_runs
        )
        VALUES (?, ?, ?, 1)

        ON CONFLICT(repo_name)
        DO UPDATE SET
            status = excluded.status,
            started_at = excluded.started_at,
            total_runs = total_runs + 1
    """, (
        repo_name,
        status,
        started_at
    ))

    conn.commit()
    conn.close()


def mark_repository_completed(repo_name: str, duration: float):

    conn = _get_connection()
    cursor = conn.cursor()

    completed_at = int(time.time())

    cursor.execute("""
        UPDATE repository_executions
        SET
            status = 'completed',
            completed_at = ?,
            duration = ?
        WHERE repo_name = ?
    """, (
        completed_at,
        duration,
        repo_name
    ))

    conn.commit()
    conn.close()


def mark_repository_failed(
    repo_name: str,
    error_type: str,
    error_message: str,
    duration: float = 0.0
):
    """
    Mark a repository execution as failed.

    Bug 5 fix: also sets completed_at and duration so the UI
    can correctly display when the failure happened and how long
    it ran before failing.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    completed_at = int(time.time())

    cursor.execute("""
        UPDATE repository_executions
        SET
            status = 'failed',
            completed_at = ?,
            duration = ?,
            error_type = ?,
            error_message = ?
        WHERE repo_name = ?
    """, (
        completed_at,
        duration,
        error_type,
        error_message,
        repo_name
    ))

    conn.commit()
    conn.close()


def get_all_repository_executions():

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM repository_executions
        ORDER BY started_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [dict(r) for r in rows]


def delete_repository_execution(repo_name: str):

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM repository_executions
        WHERE repo_name = ?
    """, (repo_name,))

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# --------------------------------------------------
# REPOSITORY CACHE
# --------------------------------------------------

def save_repositories(repositories):

    conn = _get_connection()
    cursor = conn.cursor()

    for repo in repositories:

        cursor.execute("""
            INSERT OR REPLACE INTO repositories (
                name,
                description,
                default_branch,
                updated_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            repo.get("name"),
            repo.get("description"),
            repo.get("default_branch"),
            repo.get("updated_at")
        ))

    conn.commit()
    conn.close()


def get_repositories_from_db():

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM repositories
        ORDER BY name ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [dict(r) for r in rows]
