# src/Pages/Password.jsx

> **Source File:** [src/Pages/Password.jsx](https://github.com/test-company-prowiz/maxify_frontend/blob/main/src/Pages/Password.jsx)  
> **Repository:** `maxify_frontend`  
> **Branch:** `main`

# src/Pages/Password.jsx

### Overview
This file defines the `PasswordPageReset` React component, which provides a user interface for resetting a password. It allows users to submit a new password using a token extracted from the URL, communicating with a backend API to finalize the password change.

### Architecture & Role
This file functions as a client-side user interface component within a React application. It resides in the presentation layer, specifically a "Page" level component, responsible for rendering the password reset form and handling user interactions to initiate an API call for password modification. It is a direct consumer of backend API services.

### Key Components
*   **`PasswordPageReset`**: The main functional React component that renders the password reset form.
    *   Utilizes `useParams` to extract a reset `token` from the URL.
    *   Manages loading state (`loading`) and UI visibility (`isPassVisible`, `emailField`, `successPage`) using `useState` hooks.
    *   Integrates `react-hook-form` for form management, validation, and submission handling via `register` and `handleSubmit`.
    *   Defines `notify` and `successNotify` functions for displaying toast messages using `react-toastify`.
    *   **`onSubmit(data)`**: An asynchronous function that executes on form submission. It sends a `POST` request to the backend API (`/auth/resetpassword/{token}`) with the new password. Handles both success and error responses by updating loading state and showing toast notifications.

### Execution Flow / Behavior
1.  When the `PasswordPageReset` component mounts, it extracts a `token` from the URL parameters using `useParams`.
2.  The component renders a form prompting the user to enter a new password.
3.  Upon user submission of the form, the `handleSubmit` function from `react-hook-form` invokes the `onSubmit` handler.
4.  The `onSubmit` handler sets the `loading` state to `true`, which displays a loading spinner to the user.
5.  An `axios.post` request is made to the configured API endpoint (`${API}/auth/resetpassword/${token}`) with the new password.
6.  If the API call is successful:
    *   The `loading` state is set to `false`.
    *   A success toast notification ("Password Changed Successfully") is displayed.
7.  If the API call fails (e.g., due to an invalid token or network error):
    *   The `loading` state is set to `false`.
    *   An error toast notification is displayed, often including specific details from the API response (`err.response.data.detail`).
8.  The page also provides a "Back to Login" link using `react-router-dom`'s `Link` component.

### Dependencies
*   **`react`**: Core library for building user interfaces.
*   **`useState`**: React hook for managing component local state.
*   **`logo`**: An image asset (`../Assets/logo.png`) used for branding.
*   **`react-hook-form`**: Library for efficient and flexible form validation and management.
*   **`react-router-dom`**: Provides routing capabilities, specifically `Link` for navigation, `useNavigate` for programmatic navigation, and `useParams` for extracting URL parameters.
*   **`App, API`**: Imports the `API` constant from `../App`, which defines the base URL for API requests.
*   **`axios`**: A promise-based HTTP client for making API requests.
*   **`react-toastify`**: Library for displaying toast notifications to the user.
*   **`antd`**: A UI library, specifically importing `Spin` for loading indicators and `LoadingOutlined` icon.

### Design Notes
*   The component leverages `react-hook-form` for streamlined form state management and validation, reducing manual state handling.
*   API communication is handled via `axios`, centralizing HTTP requests.
*   User feedback for success/failure is provided through `react-toastify` notifications.
*   A global `API` constant is imported from `../App`, suggesting a centralized configuration for the backend endpoint.
*   The use of `useParams` implies that the password reset mechanism relies on a token passed directly in the URL, a common pattern for token-based password resets.
*   The code contains significant commented-out sections (e.g., `setSuccessPage`, alternative `onSubmit` logic, different form structures) indicating either work in progress, removed features, or alternative implementation attempts. The currently active logic does not navigate to `/login` immediately on success, unlike the commented-out code.

### Diagram
```mermaid
graph TD
UserAccessesURL[User Accesses URL with Token] --> PasswordPageResetComponent[PasswordPageReset Component]
PasswordPageResetComponent --> ExtractToken[Extract Token from URL]
PasswordPageResetComponent --> DisplayPasswordForm[Display New Password Form]
DisplayPasswordForm --> UserInput[User Enters New Password]
UserInput --> FormSubmit[Submit Form]
FormSubmit --> SetLoadingTrue[Set Loading State to True]
SetLoadingTrue --> APIRequest[Axios POST to /auth/resetpassword/token]
APIRequest -- Success --> ShowSuccessToast[Show "Password Changed Successfully" Toast]
APIRequest -- Failure --> ShowErrorToast[Show Error Toast]
ShowSuccessToast --> SetLoadingFalseSuccess[Set Loading State to False]
ShowErrorToast --> SetLoadingFalseError[Set Loading State to False]
```