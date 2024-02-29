
# New Templates Glossary

This document serves as a glossary for the templates directory structure of the project.

## Directory Structure

- `/templates`
  - **/layouts**: Contains base templates and shared layouts used across the site. Simply put, it defines the overall structure or skeleton of the application (less frequently revised).
    - `base.html`: The main base template from which all other templates inherit.
    - `/admin`
      - `admin-base.html`: A specialized layout for admin pages. It extends `base.html` but can include additional styling, scripts, or components specific to admin interfaces to enhance security and organization.
      - `withnav.html`: A variation of the base layout that includes a sidebar.
    - `/error`: Templates for handling HTTP errors
  - **/components**: Houses reusable UI components that can be included in multiple templates and can be tailored with different content or links depending on the context.(more frequently revised or customized)
    - `header.html`: Template for the site's header, included in `base.html`.
    - `footer.html`: Template for the site's footer, included in `base.html`.
  - **/partials**: For smaller, reusable pieces of templates, like navigation breadcrumbs or pagination controls we could put this folder into components but if it's more specific to layouts, we can move it into that folder as a sub directory
  - **/views** (or **/pages**): Individual page templates that use the base layouts, components, and partials to present content.

### Best Practices

- Use **inheritance** (`{% extends %}`) to build on base layouts.
- Employ **components** (`{% include %}`) for reusable UI elements to keep the code DRY and facilitate easier updates.

### Notes
- Macro json files are just guides on how to structure a dict. It's not actually being used as data being passed to components
