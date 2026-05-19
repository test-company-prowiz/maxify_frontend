# src/Components/test.py

> **Source File:** [src/Components/test.py](https://github.com/test-company-prowiz/maxify_frontend/blob/main/src/Components/test.py)
> **Repository:** `maxify_frontend`
> **Branch:** `main`

# src/Components/test.py

### Overview
This file provides the data access layer for the application, managing an SQLite database named `app_settings.db`. It handles persistent storage for application settings, documentation job queues, tracked documented files, content-addressable documentation blobs, and repository metadata. It includes database initialization, schema migrations, and CRUD operations for these entities.

### Architecture & Role
This file functions as the persistence layer, specifically a data access object (DAO) for the application's SQLite database. It abstracts direct database interactions, providing a structured API for managing application state and data. It sits within the `Components` directory, indicating its role as a core utility component that other parts of the system (e.g., API endpoints, background workers) interact with for data storage and retrieval.

### Key Components
-   `DB_FILE`: Constant defining the SQLite database file path.
-   `_settings_cache`: An in-memory cache for `settings` data, designed to reduce database load with a `CACHE_TTL`.
-   `_get_connection()`: Establishes and configures a SQLite database connection, enabling WAL journal mode and row factory for dictionary-like access.
-   `init_db()`: Initializes the database by creating all necessary tables (`settings`, `settings_versions`, `repository_executions`, `repositories`, `job_queue`, `documented_files`, `doc_blobs`) and applies idempotent schema migrations.
-   `_migrate_documented_files_add_branch()`: Migration logic to add a `branch` column to the `documented_files` table and update its unique constraint.
-   `_migrate_job_queue_add_branch_columns()`: Migration logic to add `branch` and `force_regenerate` columns to the `job_queue` table.
-   `get_settings()`: Retrieves application settings, utilizing the in-memory cache and defaulting the prompt template if not configured. It also associates current settings with their version metadata.
-   `save_settings()`: Persists application settings, creating a new version entry in `settings_versions` if changes are detected, and updates the active `settings`.
-   `restore_version()`: Reverts the active application settings to a previously saved configuration snapshot from `settings_versions`.
-   `get_versions()`: Fetches all active (non-deleted) historical versions of application settings.
-   `soft_delete_version()`: Marks a specific settings version as deleted.
-   `enqueue_job()`: Adds a new documentation task to the `job_queue`, including repository, branch, selected files, and regeneration flags.
-   `fetch_next_job()`: Atomically claims and returns the next pending job from the `job_queue` to prevent concurrent processing.
-   `reset_stuck_jobs()` / `reset_stale_jobs()`: Self-healing functions to reset `in_progress` jobs in the `job_queue` that are likely orphaned due to server restarts or prolonged inactivity.
-   `upsert_repository_execution()`: Records or updates the status of a documentation run for a specific repository.
-   `mark_repository_completed()` / `mark_repository_failed()`: Updates the status and details of a repository documentation execution.
-   `get_documented_sha()` / `get_all_documented_shas()`: Retrieves the SHA of documented files for a given repository and branch.
-   `save_documented_file()`: Records the `blob_sha` for a file that has been documented on a specific branch.
-   `get_doc_blob()` / `save_doc_blob()`: Manages a cache for raw documentation content, keyed by content-addressable GitHub `blob_sha` for deduplication across branches and repositories.

### Execution Flow / Behavior
1.  **Database Setup**: Upon application startup, `init_db()` is invoked to ensure the database schema is in place. This involves creating tables if they don't exist and running any pending schema migrations to update existing tables.
2.  **Settings Access**: When application settings are requested via `get_settings()`, the system first checks an in-memory cache. If the settings are cached and not stale, they are returned immediately. Otherwise, the settings are loaded from the `settings` table, enriched with version metadata from `settings_versions`, cached, and then returned.
3.  **Settings Modification**: Calls to `save_settings()` trigger a comparison with current settings. If changes are detected, a new version snapshot is stored in `settings_versions`, and the `settings` table is updated. `restore_version()` directly applies a historical configuration.
4.  **Job Processing**: Documentation jobs are added to the `job_queue` via `enqueue_job()`. Background workers or job processors use `fetch_next_job()` to atomically retrieve and claim pending jobs, marking them `in_progress`. Self-healing functions (`reset_stuck_jobs`, `reset_stale_jobs`) can reset `in_progress` jobs back to `pending` if they become unresponsive.
5.  **Documentation Tracking**: The system tracks documented files using `save_documented_file()`, associating a `blob_sha` with a `(repo_name, branch, file_path)` tuple. This allows for branch-specific documentation tracking.
6.  **Content Deduplication**: Raw documentation content generated by the AI is cached in `doc_blobs` using the file's `blob_sha`. `get_doc_blob()` retrieves this content, enabling reuse across different files or branches with identical content, reducing redundant AI calls.
7.  **Repository Execution Monitoring**: Functions like `upsert_repository_execution()`, `mark_repository_completed()`, and `mark_repository_failed()` update the `repository_executions` table to track the status, duration, and outcomes of documentation runs for entire repositories.

### Dependencies
-   `sqlite3`: Core Python module for interacting with the SQLite database.
-   `json`: Used for serializing and deserializing structured data (e.g., `selected_files`, `config_snapshot`) to/from database text fields.
-   `time`: Provides functions for timestamps, notably `time.time()` for Unix epoch timestamps used in job tracking and cache management.
-   `logging`: Standard library for logging operational messages and migration progress.
-   `datetime`: Used for ISO-formatted UTC timestamps for `documented_at`, `updated_at`, and `generated_at` fields.
-   `typing`: Provides type hints for improved code readability and maintainability.
-   `prompt_templates.get_full_system_prompt`: An internal module dependency used to retrieve a default system prompt template if one is not explicitly configured in settings.

### Design Notes
-   **WAL Mode**: The database is configured with `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;` for improved concurrency and performance, particularly important for multi-threaded access (enabled by `check_same_thread=False`).
-   **Idempotent Migrations**: Schema migration functions are designed to be idempotent, preventing errors if run multiple times, which simplifies database initialization logic.
-   **Branch-Aware Tracking**: The `documented_files` and `job_queue` tables, along with their associated functions, explicitly incorporate a `branch` column. This enables the system to manage documentation and jobs distinctly for different branches within the same repository.
-   **Content-Addressable Cache**: The `doc_blobs` table leverages GitHub's content-addressable `blob_sha` to store raw generated documentation. This design choice effectively deduplicates documentation efforts, as identical file content across branches or repositories will only be processed once by the AI.
-   **Settings Versioning**: The `settings_versions` table provides a robust audit trail and rollback capability for application configuration, enhancing operational safety.
-   **In-Memory Caching**: The `_settings_cache` mechanism reduces database load for frequently accessed settings, improving read performance.
-   **Atomic Operations**: `fetch_next_job()` uses `UPDATE ... RETURNING *` for atomic job claiming, essential for concurrent job processing without race conditions.
-   **Self-Healing**: The inclusion of `reset_stuck_jobs`, `reset_stale_jobs`, and `reset_stale_repository_executions` demonstrates a focus on system resilience by automatically recovering from orphaned `in_progress` states caused by unexpected server shutdowns or timeouts.

### Diagram
None significant.