# Manual Accessibility Testing Checklist

## 1. Structure and Semantics

### Headings:
- Verify that headings are used logically (`<h1>` to `<h6>`) to create a clear content hierarchy.
- Ensure there is only one `<h1>` per page (unless it’s a valid use case, like within `<section>` landmarks).

### Landmarks:
- Confirm the presence of ARIA landmarks (e.g., `<header>`, `<main>`, `<footer>`) for navigation.
- Use tools (e.g., Accessibility Insights, Axe) to ensure proper landmark roles.

### HTML Validity:
- Check for semantic HTML usage (e.g., `<button>` for buttons, `<a>` for links).
- Avoid using `<div>` or `<span>` for interactive elements.


## 2. Navigation and Focus

### Keyboard Navigation:
- Ensure all functionality is accessible via the keyboard (e.g., Tab, Enter, Space, Arrow Keys).
- Test for logical tab order that follows the visual reading order.

### Focus States:
- Ensure focus is visible and distinct on all interactive elements.
- Check that focus is not trapped in modal dialogs or components.

### Skip Links:
- Verify that “Skip to content” links are present and functional.


## 3. Forms and Inputs

### Labels:
- Confirm all form fields have accessible, descriptive labels (`<label>` or `aria-label`/`aria-labelledby`).
- Ensure placeholder text is not used as a label substitute.

### Error Messages:
- Check that error messages are programmatically associated with inputs and conveyed to assistive technologies.
- Verify that error messages are specific and provide actionable guidance.

### Fieldset and Legend:
- Group related inputs with `<fieldset>` and `<legend>` where appropriate.


## 4. Media and Non-Text Content

### Images:
- Ensure all meaningful images have appropriate alt text.
- Decorative images should have `alt=""` or be hidden with `role="presentation"`.

### Videos:
- Verify captions are available and accurate for all video content.
- Provide audio descriptions for videos with critical visual information.

### Audio:
- Confirm there is a way to stop, pause, or adjust the volume of any audio that plays automatically.


## 5. Color and Contrast

### Color Contrast:
- Use a contrast checker to ensure text and interactive elements meet WCAG AA requirements (4.5:1 for text, 3:1 for large text).

### Color Independence:
- Verify that color is not the sole means of conveying information (e.g., “errors in red”).

### High Contrast Modes:
- Test with browser or OS high-contrast modes to ensure proper readability.

---

## 6. Dynamic Content and Interactions

### ARIA Live Regions:
- Verify that dynamic updates are announced using `aria-live` (e.g., success messages).

### Modals and Dialogs:
- Ensure modals have proper focus management (focus should move to the modal on open and back to the trigger on close).
- Test that modals are announced properly by screen readers.

### Tooltips and Popovers:
- Ensure tooltips are accessible via keyboard and announced by assistive technologies.


## 7. Assistive Technology Compatibility

### Screen Reader Testing:
- Test the site with a screen reader (e.g., NVDA, JAWS, VoiceOver) to ensure content is announced logically.
- Verify that dynamic content (e.g., dropdowns, modals) is announced appropriately.

### Zoom and Magnification:
- Ensure the site is usable at 200% zoom without loss of functionality or content.

### Responsive Design:
- Test on different devices and orientations to verify responsive behavior is accessible.


## 8. Performance and Usability

### Loading Indicators:
- Confirm that loading indicators are announced (e.g., using `aria-live`).

### Page Titles:
- Ensure page titles are unique and descriptive of the page’s content.

### Time Limits:
- Check if users can extend or disable time limits where applicable.


## 9. WCAG Success Criteria Coverage

### Review WCAG 2.1 (or 2.2 if applicable) Success Criteria:
- **Level A**: Must-have minimum requirements.
- **Level AA**: Commonly required for legal compliance.
- **Level AAA**: Optional for enhanced accessibility.


## Tools to Assist Manual Testing

### Browser Extensions:
- [Axe DevTools](https://www.deque.com/axe/)
- [WAVE](https://wave.webaim.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Screen Readers:
- **NVDA** (Windows)
- **VoiceOver** (macOS/iOS)
- **TalkBack** (Android)

### Contrast Checkers:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Color Contrast Analyzer](https://developer.paciellogroup.com/resources/contrastanalyser/)

### Keyboard Navigation:
- Test tabbing through the site manually.
