# package.json

> **Source File:** [package.json](https://github.com/maxify_frontend/blob/main/package.json)  
> **Repository:** `maxify_frontend`  
> **Branch:** `main`

### Overview
This file serves as the manifest for the `dashworx` project. It defines metadata, development and production dependencies, and scripts for managing the application's lifecycle, including starting, building, testing, and ejecting from the Create React App configuration.

### Architecture & Role
Architecturally, `package.json` resides at the root level of the project, serving as the central configuration point for the Node.js package manager (npm or Yarn). It dictates the project's foundational requirements and operational commands for a frontend React application built with `react-scripts`. It does not contain application logic but specifies the environment and tools required for the application to function and be developed.

### Key Components
*   **name**: `dashworx` - The identifier for this project.
*   **version**: `0.1.0` - Current version of the project.
*   **private**: `true` - Indicates that the package is not intended for publication to a public npm registry.
*   **dependencies**: Lists runtime dependencies essential for the application to function in production.
*   **devDependencies**: Lists development-only dependencies, such as build tools, testing utilities, and linters.
*   **scripts**: Defines various command-line scripts to automate common development tasks (`start`, `build`, `test`, `eject`).
*   **eslintConfig**: Configures ESLint, specifying which linting rulesets to extend.
*   **browserslist**: Defines target browser compatibility for the project, used by tools like Babel and Autoprefixer.

### Execution Flow / Behavior
The `scripts` section defines commands executed via `npm run <script-name>`.
*   `npm start`: Initiates a development server, typically with hot-reloading, using `react-scripts start`.
*   `npm build`: Compiles the React application into static files for deployment, using `react-scripts build`.
*   `npm test`: Runs unit tests, typically via Jest and React Testing Library, using `react-scripts test`.
*   `npm eject`: Detaches the project from the `react-scripts` abstraction, exposing the underlying configuration files.

### Dependencies
The `dependencies` section includes:
*   **React ecosystem**: `react`, `react-dom`, `react-scripts` (Create React App), `web-vitals` (performance metrics).
*   **UI/Styling**: `antd` (Ant Design UI library), `@ant-design/icons` (Ant Design icons).
*   **Routing**: `react-router-dom` (client-side routing).
*   **State Management/Forms**: `react-hook-form` (form validation).
*   **Networking**: `axios` (HTTP client).
*   **Authentication**: `jwt-decode` (decoding JWT tokens).
*   **Notifications**: `react-toastify` (toast notifications).
*   **Testing**: `@testing-library/jest-dom`, `@testing-library/react`, `@testing-library/user-event` (for component testing).

The `devDependencies` section includes:
*   **Styling**: `tailwindcss` (CSS utility framework).

### Design Notes
The project leverages `react-scripts`, indicating an initial setup via Create React App, which abstracts common build configurations. The choice of `antd` suggests a preference for a comprehensive UI component library, while `tailwindcss` in `devDependencies` points to a hybrid styling approach or an intention to customize Ant Design with utility classes. The inclusion of `axios`, `jwt-decode`, and `react-router-dom` indicates a single-page application (SPA) architecture with API interactions and client-side authentication.

### Diagram (Optional)
None significant.