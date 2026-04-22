# src/Components/Header.jsx

> **Source File:** [src/Components/Header.jsx](https://github.com/test-company-prowiz/maxify_frontend/blob/main/src/Components/Header.jsx)
> **Repository:** `maxify_frontend`
> **Branch:** `main`

# src/Components/Header.jsx

### Overview
This file defines the `Header` React component, which provides global navigation and user account access points across the application. It displays a logo, a "My Account" dropdown, and handles routing based on user interactions.

### Architecture & Role
This component operates within the presentation layer of the frontend application. It functions as a top-level UI element, responsible for consistent branding and user interaction mechanisms. It is intended to be rendered at the root or a high-level layout component.

### Key Components
*   **Header (function component)**: The primary component responsible for rendering the application header.
*   **`useState` hook**: Manages the `hover` state for the "My Account" dropdown visibility.
*   **`useNavigate` hook**: Provided by `react-router-dom` for programmatic navigation.
*   **`isNavigatable` (prop)**: A boolean flag controlling whether certain navigation actions are active.
*   **`isHomeNav` (prop)**: A boolean flag that conditionally applies a background color to the header.

### Execution Flow / Behavior
The `Header` component renders a horizontal bar containing a logo and a "My Account" section.
*   Clicking the logo navigates to `/home` if `isNavigatable` is true.
*   Hovering over the "My Account" section reveals a dropdown menu.
*   The dropdown contains "Home", "Log Out", and "Change Password" options.
*   Clicking "Home" in the dropdown navigates to `/home` if `isNavigatable` is true.
*   Clicking "Log Out" navigates to `/login` and removes the item named "data" from `localStorage`.
*   Clicking "Change Password" navigates to `/resetpassword`.
*   The background color of the header changes based on the `isHomeNav` prop.

### Dependencies
*   **`react`**: Used for building the UI component and managing state with `useState`.
*   **`react-router-dom`**: Provides the `useNavigate` hook for client-side routing functionality.
*   **`../Assets/logo.png`**: Application logo image.
*   **`../Assets/Login_icon 1.svg`**: Icon for the login/account section.
*   **`../Assets/downArrow.svg`**: Icon for the "My Account" dropdown indicator.

### Design Notes
The component utilizes props (`isNavigatable`, `isHomeNav`) to manage behavioral and stylistic variations, promoting reusability. The `localStorage.removeItem("data")` call upon logout suggests a simple client-side session management approach. The dropdown uses direct CSS positioning and hover states, which could be refactored into a more robust, accessible dropdown component for complex interactions.

### Diagram
None significant.