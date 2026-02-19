# package.json

### Overview
This file serves as the manifest for a Node.js project, specifically a React application. It defines metadata about the project, lists its direct dependencies (both production and development), and specifies executable scripts for common tasks like starting, building, and testing the application.

### Architecture & Role
Architecturally, `package.json` resides at the root of the frontend application layer. It acts as the primary configuration entry point for package managers (like `npm` or `yarn`) to understand the project's requirements, install necessary libraries, and execute predefined commands. It is crucial for project setup, continuous integration, and local development environments.

### Key Components
*   **`name`**: Identifies the project as "dashworx".
*   **`version`**: Specifies the current version of the project (0.1.0).
*   **`private`**: Set to `true`, indicating that this package is not intended for publication to a public registry.
*   **`dependencies`**: Lists runtime dependencies required for the application to function in production.
*   **`devDependencies`**: Lists dependencies required only for development and build processes, not for the application's runtime.
*   **`scripts`**: Defines command-line aliases for executing common development and build tasks.
*   **`eslintConfig`**: Configures ESLint, specifying which linting rulesets to extend for code quality.
*   **`browserslist`**: Defines the target browser environments for transpilation and polyfilling, optimizing build output.

### Execution Flow / Behavior
When a package manager executes commands like `npm install` or `npm run <script-name>`, it consults this file.
*   `npm install`: Reads `dependencies` and `devDependencies` to fetch and install all required packages into the `node_modules` directory.
*   `npm run start`: Executes `react-scripts start`, which typically launches a development server, compiles the React application, and serves it for local development.
*   `npm run build`: Executes `react-scripts build`, which compiles the React application into static assets suitable for production deployment.
*   `npm run test`: Executes `react-scripts test`, running the project's test suite.

### Dependencies
The file declares a range of essential dependencies for a modern React application:
*   **`react`**, **`react-dom`**: Core libraries for building user interfaces with React.
*   **`react-router-dom`**: Provides declarative routing for React applications.
*   **`antd`**, **`@ant-design/icons`**: Ant Design UI library and its associated icons, used for building UI components.
*   **`axios`**: A promise-based HTTP client for making API requests.
*   **`jwt-decode`**: For decoding JSON Web Tokens, likely used for authentication.
*   **`react-hook-form`**: A library for form validation.
*   **`react-scripts`**: A set of scripts provided by Create React App for development, building, and testing.
*   **`react-toastify`**: For displaying toast notifications to the user.
*   **`tailwindcss` (devDependency)**: A utility-first CSS framework used during development for styling.
*   **`@testing-library/*`**: Libraries for testing React components.

### Design Notes
The use of `react-scripts` indicates that this project was likely bootstrapped with Create React App (CRA). This simplifies the build configuration by abstracting away webpack and Babel settings. The `private: true` field prevents accidental publication of this application to a public npm registry, which is standard practice for frontend applications not intended as reusable libraries. The inclusion of `browserslist` ensures that the compiled code is compatible with the specified target browsers, balancing modern features with wider compatibility.

### Diagram (Optional)
None significant.