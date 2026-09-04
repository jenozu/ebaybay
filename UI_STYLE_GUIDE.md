# eBayBay — UI Style Guide

**Status:** Approved visual direction for MVP  
**Purpose:** Keep the eBayBay interface visually consistent as Phase 1 and later UI work is implemented.

This style guide is based on the provided Treat Tab reference design and color palette. The goal is to reuse the same playful neo-brutalist visual language while adapting it to an eBay listing-assistant workflow.

## Core visual direction

Use a **neo-brutalist candy / pastel UI** with:

- thick black borders;
- solid black offset shadows;
- rounded cards and buttons;
- bright pastel panels;
- high-contrast black typography;
- restrained use of pink/cyan/lilac accents;
- simple, bold dashboard layouts;
- clear mobile-friendly touch targets;
- explicit visual states for Draft, Ready, Error, Published, etc.

The interface should feel friendly and distinctive without becoming visually noisy. Functional listing data remains the priority.

---

# Color palette

| Token | Color Name | Hex | Primary Usage |
|---|---|---:|---|
| `--brand-pink` | Bubblegum Pink | `#FFD8E8` | App canvas, tinted containers, brand background |
| `--ink` | Neo-Brutalist Solid Black | `#000000` | Borders, shadows, headings, nav/header bars |
| `--surface` | Pure White | `#FFFFFF` | Cards, forms, sheets, primary content surfaces |
| `--cta-cyan` | Pastel Cyan / Electric Sky | `#9BE9FB` | Primary CTA buttons, active tabs, highlight cards |
| `--cta-cyan-hover` | Soft Cyan | `#83DFEF` | Hover/pressed primary CTA state |
| `--lilac` | Pastel Lilac / Lavender | `#FAE8FF` | Secondary actions, chips, soft supporting cards |
| `--ice-blue` | Soft Ice Blue | `#EBF8FF` | Hover transitions, selected pills, subtle information backgrounds |
| `--rose-muted` | Candy Rose Muted | `#F6BED5` | Secondary pink accents and borders |
| `--danger` | Danger Crimson | `#CC0000` | Errors, destructive warnings |
| `--danger-bright` | Bright Danger Red | `#E02424` | Critical alerts and delete actions |
| `--neutral-light` | Off White | `#FBFBFB` | Input backgrounds / page sections |
| `--neutral-divider` | Neutral Light Grey | `#F1F1F1` | Dividers / subtle separators |

## Suggested CSS variables

```css
:root {
  --brand-pink: #FFD8E8;
  --ink: #000000;
  --surface: #FFFFFF;
  --cta-cyan: #9BE9FB;
  --cta-cyan-hover: #83DFEF;
  --lilac: #FAE8FF;
  --ice-blue: #EBF8FF;
  --rose-muted: #F6BED5;
  --danger: #CC0000;
  --danger-bright: #E02424;
  --neutral-light: #FBFBFB;
  --neutral-divider: #F1F1F1;
}
```

---

# Neo-brutalist component rules

## Borders

Primary cards, inputs and buttons should generally use:

```css
border: 2px solid var(--ink);
```

Use `4px` borders only for major framing elements or deliberate emphasis.

## Shadows

Default elevated component:

```css
box-shadow: 4px 4px 0 var(--ink);
```

Pressed state should reduce/remove the offset so buttons feel physically pressed:

```css
transform: translate(2px, 2px);
box-shadow: 2px 2px 0 var(--ink);
```

## Border radius

Keep rounded geometry similar to the reference:

```text
Small pills / chips:       999px
Inputs:                    10–12px
Buttons:                   12–16px
Cards:                     14–18px
Major panels:              16–22px
```

Avoid ultra-soft floating cards without borders; black outlines are part of the identity.

---

# Typography

Use a clean sans-serif stack for MVP. Do not block the project on a custom font.

Suggested stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
             "Segoe UI", sans-serif;
```

Use:

- strong bold headings;
- compact uppercase section labels sparingly;
- clear hierarchy over decorative typography;
- black text for normal content wherever possible.

---

# Application layout guidance

## Page canvas

Primary app background:

```css
background: var(--brand-pink);
```

Long-form edit/review screens may place a white or off-white main workspace over the pink canvas to preserve readability.

## Header / navigation

Preferred pattern:

- black header/nav background;
- white text;
- small cyan/pink status badge;
- active navigation item uses cyan fill with black text;
- mobile bottom navigation may follow the same Treat Tab reference style.

## Cards

Use white as the default data surface. Reserve cyan, pink and lilac for category differentiation or important actions rather than coloring every card.

Suggested dashboard mapping:

```text
Draft / New Listing             Pastel Cyan
Needs Review                    Bubblegum Pink / muted rose
Ready                           Pastel Lilac or cyan
Published                       White + cyan status badge
Failed / Validation Error       White + red warning treatment
```

---

# Button hierarchy

## Primary action

Examples:

- Save Draft
- Analyze Product
- Validate
- Approve Listing
- Stage on eBay

Use:

```text
Background: #9BE9FB
Text:       #000000
Border:     2px solid #000000
Shadow:     4px 4px 0 #000000
```

Hover/pressed fill: `#83DFEF`.

## Secondary action

Examples:

- Regenerate
- Edit
- Back
- Cancel

Use white or `#FAE8FF` with black border/shadow.

## Destructive action

Examples:

- Delete Draft
- Disconnect eBay

Use white or pale background with `#CC0000` / `#E02424` text/icon, while retaining a black border where appropriate. Avoid large solid-red areas unless the action is genuinely critical.

## Publish action

`PUBLISH TO EBAY` is deliberately distinct from ordinary actions.

Recommended treatment:

- black background;
- white text;
- cyan or pink confirmation accent;
- explicit confirmation modal before performing the call.

Never make Publish visually interchangeable with Save Draft.

---

# Form controls

Inputs should use:

```text
Background: #FBFBFB or #FFFFFF
Border:     2px solid #000000
Text:       #000000
Radius:     ~12px
```

Focus state can use cyan fill/outline, but preserve strong contrast.

Missing required eBay values should be visually obvious, for example:

```text
⚠ REQUIRED BEFORE PUBLISH
```

Use red only for actual errors/requirements, not ordinary helper text.

---

# Listing review screen visual priorities

The review screen is the most important interface in the MVP. Use the visual theme without sacrificing scanability.

Recommended grouping:

```text
PHOTOS
PRODUCT IDENTITY
CATEGORY
CONDITION
TITLE
PRICE + ACTIVE COMPARABLES
ITEM SPECIFICS
DESCRIPTION
VALIDATION
```

Each group can be a thick-bordered card. Primary editable data surfaces should remain mostly white, with cyan/pink/lilac used for headings, badges and action panels.

Suggested status chips:

```text
DRAFT           Pink
ANALYZING       Lilac
NEEDS REVIEW    Pink / rose
READY           Cyan
EBAY STAGED     Ice blue / cyan
PUBLISHED       Cyan + strong black outline
FAILED          Red treatment
```

---

# Responsive/mobile requirements

The provided visual reference is mobile-oriented, and eBayBay should remain practical on a phone.

- Minimum comfortable touch target: ~44px.
- Avoid horizontal scrolling on forms.
- Stack dashboard cards to one column on narrow screens.
- Keep important action buttons full-width or large on mobile.
- A bottom navigation bar is acceptable for core views such as Dashboard, Listings and Settings.
- Review/edit screens may use sticky Save/Validate actions where useful.

Desktop layouts should expand rather than completely change the design language.

---

# Accessibility / usability constraints

The theme does not override usability.

- Maintain sufficient text/background contrast.
- Do not communicate status by color alone; always include text/icon labels.
- Preserve visible keyboard focus states.
- Use semantic labels for form fields.
- Error messages must explain the problem in text.
- Do not use pastel text on white backgrounds where contrast becomes weak.

---

# Implementation rule

When Phase 1 introduces the real templates/static assets, implement these values centrally rather than hard-coding colors throughout individual templates.

Preferred location:

```text
app/static/css/theme.css
```

with CSS custom properties from this document.

All new UI work should consult this file before inventing additional brand colors. New colors may be added only when there is a functional reason and they should be documented here.

---

# Approved MVP design baseline

- [x] Bubblegum-pink brand canvas selected.
- [x] Neo-brutalist black borders/shadows selected.
- [x] Pastel cyan primary CTA selected.
- [x] Lilac/ice-blue secondary palette selected.
- [x] Danger/error red palette selected.
- [x] White/off-white data surfaces selected.
- [x] Mobile-friendly card/button language selected.
- [x] Human-review/publish actions retain strong visual distinction.

The actual UI components remain a Phase 1 implementation task; this document defines their approved visual system in advance.
