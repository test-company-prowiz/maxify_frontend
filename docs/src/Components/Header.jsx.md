# src/Components/Header.jsx

> **Source File:** [src/Components/Header.jsx](https://github.com/test-company-prowiz/maxify_frontend/blob/main/src/Components/Header.jsx)
> **Repository:** `maxify_frontend`
> **Branch:** `main`

# src/Components/Header.jsx

### Overview
This file defines the `Header` React functional component, which provides a consistent navigation bar for the application. It includes the application logo, a "My Account" dropdown menu for user-related actions, and handles programmatic navigation.

### Architecture & Role
This component resides in the Presentation Layer, specifically within the UI components directory. Its role is to render the top-level persistent navigation and user interaction elements, providing a consistent header across various application pages.

### Key Components
*   **`Header` Functional Component**: The main React component responsible for rendering the header UI. It accepts `isNavigatable` and `isHomeNav` props to control navigation behavior and styling.
*   **`useState` Hook**: Manages the `hover` state to control the visibility of the "My Account" dropdown menu.
*   **`useNavigate` Hook**: Provided by `react-router-dom`, this hook enables programmatic navigation to different routes within the application.

### Execution Flow / Behavior
The `Header` component renders a top navigation bar.
1.  It receives `isNavigatable` and `isHomeNav` boolean props, which dictate whether the logo and "Home" menu item can trigger navigation and control the header's background color, respectively.
2.  The application logo, when clicked, navigates to the `/home` route if `isNavigatable` is true.
3.  A "My Account" section displays a login icon, text, and a down arrow. Hovering over this section toggles a `hover` state.
4.  When `hover` is true, a dropdown menu appears containing "Home", "Log Out", and "Change Password" options.
    *   "Home" navigates to `/home` if `isNavigatable` is true.
    *   "Log Out" navigates to `/login` and clears the `data` item from `localStorage`.
    *   "Change Password" navigates to `/resetpassword`.
5.  The dropdown menu also uses `onMouseOver` and `onMouseOut` to maintain its visibility while the user's mouse is within its bounds.

### Dependencies
*   **`react`**: Core library for building user interfaces, specifically `useState` for managing component state.
*   **`react-router-dom`**: Provides `useNavigate` for routing and programmatic navigation within the application.
*   **Local Assets**:
    *   `../Assets/logo.png`: Application logo image.
    *   `../Assets/Login_icon 1.svg`: Icon for the "My Account" section.
    *   `../Assets/downArrow.svg`: Icon for the "My Account" dropdown indicator.

### Design Notes
*   The component uses Tailwind CSS classes directly within JSX for styling, making it highly coupled to the styling framework.
*   Conditional rendering (`{hover && ...}`) is used for the dropdown menu, managed by local component state.
*   The `isNavigatable` prop provides a mechanism to disable certain navigation actions (e.g., when a user is in a non-navigable flow like an onboarding wizard).
*   The `isHomeNav` prop allows for dynamic styling of the header based on the current page context.
*   Direct manipulation of `localStorage` for logout is handled within the component, which might be centralized in a larger application for better state management.

### Diagram
None significant.