---
name: rule-frontend
description: "Rules for writing or changing any UI code: components, pages, layouts, styles, forms, client state, data fetching in the browser, and UI bugs. Load whenever you create or edit a .tsx/.jsx/.vue/.svelte/.css/.scss file or anything under components/, pages/, or app/, even when the user never says 'frontend', 'UI', or 'design'. /simply:build reads it before touching UI; backend, schema, and endpoint work use rule-backend, rule-db, and rule-api-design instead."
paths:
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*.astro"
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.sass"
  - "**/*.less"
  - "**/components/**"
  - "**/pages/**"
  - "**/app/**/*.tsx"
  - "**/app/**/*.jsx"
  - "**/views/**"
  - "**/layouts/**"
  - "**/styles/**"
---

# Frontend Rules

Rules that change decisions when writing or changing UI. The project's own `CLAUDE.md` conventions win over these rules when they conflict.

## Reuse before writing

- Search the codebase for an existing component, hook, or utility before creating one; extend it with a prop rather than copy it — why: two near-identical components drift apart and every fix lands in only one.
- Use the project's existing UI library, icon set, and styling method; never introduce a second one — why: two systems double the bundle and split the visual language.
- Don't add a dependency for something under ~50 lines (debounce, classnames, date formatting the platform `Intl` already does) — why: each package adds bundle weight, update churn, and supply-chain risk.
- Prefer the native element (`<button>`, `<a href>`, `<dialog>`, `<details>`, `<input type="date">`) over a div rebuilt with handlers — why: native elements bring keyboard, focus, and screen-reader behavior for free.
- Copy the patterns of the nearest sibling file (file layout, naming, export style, test placement) — why: consistency beats any local improvement a reviewer has to learn.

## States

- Every view that loads data renders loading, empty, and error states — why: the happy path is the one state users see least during failures.
- Loading shows a skeleton or spinner only after ~200 ms, and never blanks content already on screen — why: instant flashes read as flicker; blanking loses the user's place.
- Error state says what failed in plain words and offers a retry; never render a raw error object or stack — why: users can act on "Couldn't load orders. Retry", not on `[object Object]`.
- Empty state says why it is empty and gives the next action (create, clear filters) — why: a blank area looks like a bug.
- Disable submit buttons while a mutation is in flight and show progress on the button — why: double clicks create duplicate records.
- Long text, missing images, 0 items, 1 item, and 1,000 items all render without breaking layout — why: real data is never the three tidy rows in the mockup.

## Accessibility

- Every interactive element is reachable and operable by keyboard (Tab, Shift+Tab, Enter, Space, Escape for overlays) — why: keyboard users and many assistive tools have no mouse.
- Focus is always visible; never `outline: none` without a replacement `:focus-visible` style — why: without it keyboard users lose their place.
- Text contrast ≥ 4.5:1 (3:1 for ≥ 24px text or ≥ 18.66px bold); UI borders and icons ≥ 3:1 — why: WCAG AA; below it text is unreadable in sunlight or with low vision.
- Touch targets ≥ 44×44 px, with ≥ 8 px between adjacent targets — why: smaller targets cause mis-taps on phones.
- Icon-only buttons have an accessible name (`aria-label` or visually hidden text) — why: a screen reader otherwise announces just "button".
- Images have `alt`; decorative images use `alt=""` — why: missing alt makes readers announce the file name.
- Modals and drawers trap focus, close on Escape, and return focus to the trigger on close — why: otherwise focus escapes behind the overlay or is lost on close.
- Never convey meaning by color alone; pair it with text or an icon — why: ~8% of men have color-vision deficiency.
- One `<h1>` per page and headings in order without skipping levels — why: screen-reader users navigate by headings.
- Respect `prefers-reduced-motion`: disable non-essential animation under it — why: motion triggers vestibular symptoms for some users.

## Layout and responsiveness

- Works at 360px width with no horizontal scroll; check 360, 768, and 1280 — why: 360 is the narrowest common phone; horizontal scroll hides content.
- No layout shift: reserve space for images (`width`/`height` or `aspect-ratio`) and async content (fixed-height skeletons) — why: content jumping under the cursor causes mis-clicks.
- Build mobile-first: base styles for narrow, `min-width` media queries to widen — why: it keeps the narrow case from being an afterthought.
- Use flex/grid with `gap`; no absolute positioning or magic pixel offsets for layout — why: they break at the widths you didn't check.
- Body text ≥ 16px and line length ≤ ~75 characters (`max-width: 65ch`) — why: smaller text triggers iOS zoom on inputs; long lines are hard to track.
- Set font sizes in `rem`, not `px` — why: `px` ignores the user's browser font-size setting.
- Use `min-height: 100dvh` rather than `100vh` for full-screen sections — why: `100vh` overflows behind mobile browser toolbars.

## Forms

- Every input has a visible label tied to it (`<label for>` or wrapping); placeholder is not a label — why: placeholders vanish on typing and are skipped by some readers.
- Validate on blur and on submit, not on every keystroke — why: errors shouting mid-typing punish users for being unfinished.
- Show each error next to its field, linked via `aria-describedby`, and move focus to the first invalid field on submit — why: a summary at the top alone leaves users hunting.
- Use the right `type`, `inputmode`, and `autocomplete` (`email`, `tel`, `current-password`, `one-time-code`) — why: they bring the right mobile keyboard and autofill.
- Never clear user input on a failed submit — why: retyping a long form is the top reason users abandon it.
- Client validation is for UX only; the server validates again — why: anyone can bypass the browser.
- Submit with Enter works because the form uses `<form onSubmit>` and a `type="submit"` button — why: click-only handlers break keyboard submit.

## State and data fetching

- Keep state as local as possible; lift it only when two siblings need it — why: global state makes every change ripple through unrelated components.
- Derive values during render instead of storing them in state or syncing with an effect — why: duplicated state goes stale.
- Use the project's data-fetching layer (React Query, SWR, loaders, server components) instead of `fetch` in `useEffect` — why: hand-rolled effects miss caching, dedupe, races, and cancellation.
- If you must fetch in an effect, ignore or abort stale responses on unmount and dependency change — why: a slow old response overwrites a newer one.
- Put shareable view state (filters, tab, page, search) in the URL — why: reload, back button, and shared links keep working.
- After a mutation, invalidate or update the affected queries so the UI shows the new data without a reload — why: stale lists make users repeat the action.
- List keys are stable IDs, never the array index for lists that reorder, insert, or delete — why: index keys attach state to the wrong row.
- Never put secrets or private API keys in client code or public env vars (`NEXT_PUBLIC_`, `VITE_`) — why: everything shipped to the browser is public.

## Styling

- Use the project's design tokens (CSS variables, theme, Tailwind config) for color, spacing, radius, and font; no raw hex or one-off pixel values — why: hard-coded values break theming and dark mode.
- Spacing on the project's scale (usually multiples of 4 px) — why: off-scale values make the layout look subtly wrong.
- Support dark mode wherever the project already does; check both themes — why: hard-coded light colors produce invisible text in dark mode.
- No `!important` and no inline `style` except for truly dynamic values — why: both defeat the cascade and the next override.
- Scope styles to the component (CSS modules, utility classes, scoped styles); no new global selectors on tags — why: global rules leak into unrelated pages.
- Truncate or wrap long strings deliberately (`overflow-wrap: anywhere`, `text-overflow: ellipsis` with a `title`) — why: one long URL or name otherwise blows out the layout.

## Performance

- Lazy-load below-the-fold images (`loading="lazy"`) and give them explicit dimensions; never lazy-load the largest above-the-fold image — why: lazy LCP images delay the first meaningful paint.
- Code-split routes and heavy widgets (charts, editors, maps) behind dynamic import — why: they otherwise ship on every page.
- Virtualize lists over ~200 rows — why: thousands of DOM nodes make scrolling and typing lag.
- Debounce search-as-you-type requests ~300 ms — why: a request per keystroke floods the server and races results.
- Add `memo`/`useMemo`/`useCallback` only for a measured slow render or a referential-equality need — why: unmeasured memoization adds complexity and often costs more than it saves.
- Import named functions, not whole libraries (`lodash/debounce`, not `lodash`) — why: whole-library imports bloat the bundle.

## Framework notes

- React/Next: Server Components by default in `app/`; add `"use client"` only where hooks or browser events are needed, as low in the tree as possible — why: client boundaries ship their whole subtree as JS.
- Vue: use `computed` for derived values, not `watch` writing to a ref — why: watchers that copy state go stale.
- Svelte: use `$derived` (Svelte 5) or `$:` (Svelte 4) for derived values, matching the project's version — why: mixing syntaxes breaks compilation.
- Plain HTML/CSS: the same rules apply; native elements and CSS variables replace components and theme.

## Done checklist

/simply:build Step 5 checks each item in the built-in browser and records what it saw:

1. Default state renders the change with real or seed data.
2. Empty state (0 items) shows a message and next action.
3. Loading state shows a skeleton or spinner (throttle the network or delay the mock to see it) without layout shift.
4. Error state (fail the request, e.g. stop the API or mock a 500) shows a readable message and retry.
5. Widths 360, 768, and 1280 px: no horizontal scroll, nothing clipped or overlapping.
6. Keyboard-only pass: Tab through every control in visual order, focus always visible, Enter/Space activate, Escape closes overlays.
7. Forms: submit empty, then invalid, then valid; errors show by each field and input is kept.
8. Console shows no errors or warnings introduced by the change (React key warnings, hydration mismatches, 404s).
9. Dark mode, if the project supports it: text readable, no hard-coded colors.

## Not covered

Defer to the project for: design tokens and their values, component library choice, CSS methodology, icon set, animation style, and copywriting tone. If the project has none, use what is already in the nearest file and don't introduce one.
