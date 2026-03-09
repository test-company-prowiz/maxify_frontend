# src/Components/Header.jsx

> **Source File:** [src/Components/Header.jsx](https://github.com/test-company-prowiz/maxify_frontend/blob/main/src/Components/Header.jsx)  
> **Repository:** `maxify_frontend`  
> **Branch:** `main`

# src/Components/Header.jsx

### Overview
This file defines the `Header` React component, which renders a persistent navigation and account management bar at the top of the application's user interface.

### Architecture & Role
This component is a presentational element within the React frontend application. It resides in the `Components` directory, indicating its role as a reusable UI building block. It belongs to the view layer, responsible for displaying interactive UI elements and handling basic user interactions.

### Key Components
- **`Header` function component**: The primary React component responsible for rendering the header bar.
- **`useState` hook**: Manages the `hover` state, controlling the visibility of the "My Account" dropdown menu.
- **`useNavigate` hook**: Provided by `react-router-dom`, used for programmatic navigation between different routes.
- **`logo` (image asset)**: The application's branding logo, which also functions as a navigation trigger.
- **`loginIcon` (image asset)**: An icon associated with the "My Account" section.
- **`DownArrow` (image asset)**: An icon indicating a dropdown menu for the "My Account" section.

### Execution Flow / Behavior
1. The `Header` component renders a top-level `div` containing the application logo on the left and a "My Account" interactive element on the right.
2. The logo, when clicked, navigates to the `/home` route if the `isNavigatable` prop is true.
3. Hovering over the "My Account" section triggers the display of a dropdown menu, managed by the `hover` state.
4. The dropdown menu includes options: "Home", "Log Out", and "Change Password".
5. Clicking "Home" in the dropdown navigates to `/home` if `isNavigatable` is true.
6. Clicking "Log Out" navigates to `/login` and clears an item named "data" from `localStorage`.
7. Clicking "Change Password" navigates to `/resetpassword`.
8. The header's background color is dynamically set based on the `isHomeNav` prop.

### Dependencies
- **`react`**: The core library for building UI components.
- **`react-router-dom`**: Provides the `useNavigate` hook for client-side routing.
- **`../Assets/logo.png`**: An internal image asset used for the application's logo.
- **`../Assets/Login_icon 1.svg`**: An internal SVG asset used for the login icon.
- **`../Assets/downArrow.svg`**: An internal SVG asset used for the dropdown arrow icon.

### Design Notes
- The component accepts `isNavigatable` and `isHomeNav` props, allowing external control over its navigation behavior and styling, promoting reusability in different contexts.
- The "Log Out" functionality includes `localStorage.removeItem("data")`, indicating that user session or authentication tokens are stored in `localStorage` under the key "data".
- Styling is implemented using Tailwind CSS classes directly within the JSX, following a utility-first CSS methodology.
- The hover-based dropdown interaction, while functional, may present accessibility challenges for keyboard-only users.
- Route paths are hardcoded (`/home`, `/login`, `/resetpassword`). Centralizing these paths could improve maintainability.

### Diagram
None significant.