
# New Templates Glossary

This document serves as a glossary for the templates directory structure of the project.

## Directory Structure

- `/templates`
  - `base.html`: The main base template from which all other templates inherit. This template is a combination of the old admin_template and main_template.html
  - **/layouts**: Contains base templates and shared layouts used across the site. Simply put, it defines the overall structure or skeleton of the application (less frequently revised).
    - `withnav_template.html`: A variation of the base layout that includes a sidebar.
    - `/error`: Templates for handling HTTP errors
  - **/components**: Houses reusable UI components that can be included in multiple templates and can be tailored with different content or links depending on the context.(more frequently revised or customized)
    - `header.html`: Template for the site's header, included in `base.html`.
    - `footer.html`: Template for the site's footer, included in `base.html`.
  - **/views** (or **/pages**): Individual page templates that use the base layouts, components, and partials to present content.

### Best Practices

- Use **inheritance** (`{% extends %}`) to build on base layouts.
- Employ **components** (`{% include %}`) for reusable UI elements to keep the code DRY and facilitate easier updates.

### Notes
- Macro json files are just guides on how to structure a dict. It's not actually being used as data being passed to components



### Old Layout Templates We Don't Need
- withoutnav_template.html Delete
- main_template.html Delete
- settings_templates.html Delete
- settings_nav.html (move to /new/navigation directory)
- main_nav.html (move to /new/navigation directory)
- service_navigation.html (move to /new/navigation directory)
- org_template, could be under it's own directory called /organization
- org_nav.html (move to /new/navigation directory)
- -content_template.html Delete and consolidate to base template
