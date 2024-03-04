
# New Templates Glossary

This document serves as a glossary for the templates directory structure of the project.

## Directory Structure

- `/templates`
  - `base.html`: The main base template from which all other templates inherit. This template is a combination of `main_template`, `admin_template`, `withoutnav_template` and `content_template`.
  - **/layouts**: Contains base templates and shared layouts used across the site. Simply put, it defines the overall structure or skeleton of the application (less frequently revised).
    - `withnav_template.html`: A variation of the base layout that includes a sidebar.
    - `org_template.html`: A variaton of the withnav_template
  - **/components**: Houses reusable UI components that can be included in multiple templates and can be tailored with different content or links depending on the context.(more frequently revised or customized)
    - `header.html`: Template for the site's header, included in `base.html`.
    - `footer.html`: Template for the site's footer, included in `base.html`.
  - **/views** (or **/pages**): Individual page templates that use the base layouts, components, and partials to present content.

### Best Practices

- Use **inheritance** (`{% extends %}`) to build on base layouts.
- Employ **components** (`{% include %}`) for reusable UI elements to keep the code DRY and facilitate easier updates.

### Observation Notes
- The macro-options.json files in the header and footer component act as structural guides. They aren't directly used as data passed to the usaFooter function/macro. Instead, these files outline the expected properties and provide a description of their purpose. The `usaFooter` macro component is currently only invoked in the `admin_template`, which will eventually serve as the `base.html` template. This will simplify the approach when we change the footer macros to componenets by eliminating the need to dynamically pass this data from the base.html template.



### Old Layout Templates We Don't Need
- withoutnav_template.html Delete
- main_template.html Delete
- settings_templates.html `withnav_template` can be used to replace `settings_template`.
- settings_nav.html (move to /new/navigation directory)
- main_nav.html (move to /new/navigation directory)
- service_navigation.html (move to /new/navigation directory)
- org_template, could be under it's own directory called /layout/organization
- org_nav.html (move to /new/navigation directory)
- content_template.html Delete
