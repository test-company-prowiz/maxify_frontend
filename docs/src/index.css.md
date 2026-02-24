# src/index.css

> **Source File:** [src/index.css](https://github.com/maxify_frontend/blob/main/src/index.css)  
> **Repository:** `maxify_frontend`  
> **Branch:** `main`

### Overview
This file serves as the primary entry point for global Cascading Style Sheets (CSS) definitions within the application. It integrates Tailwind CSS directives and declares custom font families for use across the user interface.

### Architecture & Role
Architecturally, this file resides at the presentation layer of the application. Its role is to establish foundational styling rules and typography configurations that are globally accessible to all components and pages. It acts as a global stylesheet, processed by the build system to generate the final CSS bundle.

### Key Components
*   **`@tailwind base;`**: Injects Tailwind's base styles, which normalize CSS and provide default styling for common HTML elements.
*   **`@tailwind components;`**: Injects Tailwind's component styles, including any custom components defined by the application.
*   **`@tailwind utilities;`**: Injects Tailwind's utility classes, which form the core of its utility-first CSS framework.
*   **`@font-face` rules**: Multiple declarations for the "Graphik" font family, linking different font weights (medium, bold, black) to local OpenType Font (.otf) files.

### Execution Flow / Behavior
When processed by a CSS preprocessor or build tool (e.g., PostCSS with Tailwind CSS plugin), the `@tailwind` directives are expanded into their respective CSS rules. The `@font-face` declarations inform the browser about the custom font files, allowing elements styled with `font-family: "Graphik"` to render using these fonts, provided the files are accessible at the specified URLs.

### Dependencies
*   **`tailwindcss`**: This file implicitly depends on the `tailwindcss` framework and its associated PostCSS plugins for the `@tailwind` directives to be correctly processed and expanded.
*   **Font Files**: It explicitly depends on the presence of the `GraphikBlack.otf`, `GraphikMedium.otf`, and `GraphikBold.otf` font files located in the `./Fonts/` directory relative to this CSS file.

### Design Notes
This file centralizes global style imports and custom font definitions, promoting consistency in typography and providing a single point of entry for the styling pipeline. The reliance on Tailwind CSS implies an adherence to a utility-first approach for styling individual components, with this file providing the foundational layer.

### Diagram (Optional)
None significant.