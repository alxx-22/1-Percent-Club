# Re-skin Prompt — "1% Club" Design System (portable)

A single, copy-paste prompt that captures **all** the branding, styling, and animation
conventions from the 1% Club dashboard so they can be re-applied to a **completely different app
with completely different data**. Everything below is data-agnostic: it describes *how the thing
looks and moves*, not what it counts. Hand this prompt (plus your own screens/data) to an AI or a
designer.

> **How to use:** paste the whole prompt. Keep §1–§7 (the design system) verbatim. Replace only
> the values called out in **§8 "Swap these for your brand"**. Feed your own screen list + data
> fields in **§9**.

---

## THE PROMPT (copy everything below this line)

You are re-skinning an application to the **"Clean Enterprise Card"** design system defined below.
Apply this look, feel, and motion language to my screens and data (given at the end). Preserve my
data semantics exactly; change only presentation. Follow every rule; when a rule and my raw content
conflict, keep the rule and adapt the content (truncate, re-label, re-group) to fit.

### 1. Design philosophy

A calm, bright, **enterprise dashboard** aesthetic: soft grey canvas, crisp white cards, one
confident brand-accent colour, generous rounding, restrained shadows, and a small set of tasteful
entrance/idle animations. Everything reads instantly; motion adds delight without noise. Think
"modern SaaS analytics dashboard," not "consumer app" and not "flat brutalist."

Core principles:
- **Card-based.** Every content group is a white rounded card on a light-grey page.
- **One accent, used sparingly.** The brand colour marks identity, primary actions, "you/mine," and
  key numbers — never large fills of body area.
- **Big numbers, small labels.** Headline metrics are large and bold; their captions are tiny,
  uppercase, letter-spaced, and muted.
- **Hierarchy by weight and colour, not borders.** 1px hairline borders and soft shadows only.
- **Motion is an entrance, not a loop.** Content animates in once; only a few tiny "alive" idle
  loops persist (halo, breathe, bob). Everything honours reduced-motion.

### 2. Colour tokens (light theme)

Use these exact roles. (Hex values are the default brand — see §8 to swap.)

**Neutrals / surfaces**
- Page background (canvas): `#f7f7f7`
- Card / surface: `#ffffff`
- Contrast fill (chips, empty avatars, muted pills): `#f2f3f4`
- Sub-card tint (nested tiles): `#fbfcfc`
- Hairline border: `#d4d8db`

**Text**
- Primary text: `#292d3a`
- Secondary text: `#3e4550`
- Muted text / captions / labels: `#606a70`

**Brand accent (green family — swap for your brand hue, keep the light→dark ramp)**
- Brand accent: `#01a982`
- Accent dark (headline numbers, deep detail): `#006750`
- Accent deep (secondary shapes): `#018f6e`
- Accent darkest (eyes/face contrast): `#06372e`
- Accent bright highlight: `#7cf5cf`
- Accent pale tint (selected/"mine" card fill): `#d1ffee`
- Accent soft tint (decoration): `#bdf5e4`

**Status**
- Warning / pending text: `#d36d00`
- Warning tint (pending chip fill): `#FBEEDF`

**Categorical data-viz palette (for up to 6 series/categories, in order):**
`#0070f8` · `#04909d` · `#009a71` · `#7764fc` · `#cc54a4` · `#d25f4b`

**Rank/medal palette (podium 1-2-3):** gold `#E0A300` (tint `#FBF1D6`) · silver `#8C99A4`
(tint `#EDEFF1`) · bronze `#B5742E` (tint `#F4E9DD`).

### 3. Typography

- **Family:** `Segoe UI` in native app text. In rendered SVG use
  `Liberation Sans, Arial, Helvetica, sans-serif` (headless renderers lack Segoe UI). Optionally
  `'Metric, Segoe UI, …'` for an exact brand match.
- **Weights:** 400 (body), 600 (labels/semibold), 700 (headings & numbers). No light weights.
- **Scale (px, at the locked canvas size):** hero number 28–30 · card metric 19–26 · card title
  15–17 · body 12–13 · label/caption 8.5–11.
- **Micro-labels:** ALL-CAPS, `font-weight:600–700`, `letter-spacing:1–2`, colour muted `#606a70`
  (e.g. `TOTAL POINTS`, `CREW ROSTER`, `EXCL PENDING`).
- **Numbers dominate.** Metric values are the largest thing in any card and use accent-dark
  `#006750`; their captions are the smallest.

### 4. Shape & elevation language

- **Cards:** corner radius `13–16`, fill `#ffffff`, `1px` border `#d4d8db`.
- **Nested tiles / sub-cards:** radius `10`, fill `#fbfcfc`, `1px` border, with a **5px accent
  left-bar** (`rx 2.5`) coloured by that tile's category, plus a small `3.5r` category dot by the
  label.
- **Chips / pills:** fully rounded (`rx` = half height, ~`8–16`), fill `#f2f3f4` (neutral) or a
  status tint; text 9–11px semibold.
- **Avatars:** circles. Filled brand `#01a982` with white initials for "you/primary"; `#f2f3f4`
  with accent-dark initials for others. Initials = first letter of first + first letter of last
  word, uppercased.
- **Soft shadow:** a **blurred black rectangle** (`fill:#000000; opacity:0.06–0.10`) of the same
  shape, offset **+4px down**, behind the card, via an SVG `feGaussianBlur stdDeviation='5'` filter.
  No hard/coloured shadows.
- **"Selected / mine" treatment:** pale accent fill `#d1ffee` + `2px` accent border `#01a982` +
  a small accent chip (e.g. `YOU`, `YOURS`) in the corner, white text on `#01a982`.
- **Section headers:** tiny uppercase muted label top-left, optional right-aligned count/summary
  (e.g. `6 members`, `Top 3`).

### 5. Layout system

- **Locked canvas** at a fixed pixel size (the reference app is **1136 × 640**; keep a single fixed
  aspect so nothing letterboxes). Page fill `#f7f7f7`.
- **Top ribbon** spanning full width, ~`52px` tall: white, `1px` bottom border; left = a `26px`
  rounded-square brand glyph (`rx 7`, accent fill, white monogram) + wordmark
  (`Name` bold `#292d3a` + `· Subtitle` regular muted); right = an identity pill (`rx 16`,
  `#f2f3f4`) with a `12r` accent avatar + name.
- **Two-column content** below the ribbon: a narrower left column (detail/"you") and a wider right
  column (leaderboard/primary viz), each a stack of cards. Swap peers occupy the **same rectangle**
  and toggle by a `Visible` rule — never move controls, never add screens for a state change.
- **Galleries** (repeating rows) have `TemplatePadding = 0`, `ShowScrollbar = false`, one image per
  row filling `Parent.TemplateWidth × TemplateHeight`. Size the template so the intended count fits
  without scrolling.
- **Landing/splash first, then enter.** Open on a branded loading screen (self-contained, no data)
  with a spinning ring; a repeating timer auto-advances the instant data is ready, plus a manual
  "Enter" button fallback. Build all data in the destination screen's `OnVisible` (runs every entry),
  not in `OnStart`.

### 6. Motion / animation system

All motion is **CSS `@keyframes` embedded in each SVG** (`<style>` block), defined **once** as a
shared stylesheet string (call it `varSvgCss`) and injected into every SVG. **Hidden start-states
live only inside `@keyframes`** so a static or reduced-motion render shows the fully settled design.
**Always** end the stylesheet with:
`@media(prefers-reduced-motion:reduce){ …all classes… {animation:none} }`.

**The shared class set (keep these names, durations, and easing):**

| Class | Effect | Spec |
|---|---|---|
| `.fu` | fade-**up** (primary entrance for cards) | `opacity 0→1`, `translateY(12px)→0`, `.55s cubic-bezier(.2,.7,.2,1) both` |
| `.fo` | fade-in (nested tiles) | `opacity 0→1`, `.5s ease-out both` |
| `.pp` | pop (avatars, medals, chips) | `opacity 0→1`, `scale(.5)→1`, `.5s cubic-bezier(.2,.7,.2,1)`, origin center |
| `.gx` | grow-x (bars) | `scaleX(0)→1`, `.65s cubic-bezier(.2,.7,.2,1)`, origin left center |
| `.rw` | row-wipe (list rows) | `opacity 0→1`, `translateX(-18px)→0`, `.5s cubic-bezier(.2,.7,.2,1)` |
| `.ring` | idle halo pulse (behind key avatar) | `scale(.75→2)`, `opacity .45→0`, `2.8s ease-out infinite` |
| `.brz` | breathe (pending chip, "live" bits) | `opacity .9↔.45`, `2.6s ease-in-out infinite` |
| `.bob` | gentle bob + tilt | `translateY(0↔-2px) rotate(-4deg↔4deg)`, `2.4s ease-in-out infinite` |

**Staggering:** reveal in reading order via inline `style='animation-delay:0.10s'` (increment
~0.06–0.08s per sibling; podium/winner reveals **last**; delays in `s` or `ms`, integer-safe).

**Screen/page transition — a branded "wipe" overlay:** a full-screen gradient panel
(accent-dark→accent, `linear-gradient`) sweeps across (`translateX(-112% → 0 → hold → 112%)`, ~1.1s)
while a few brand motifs (leaves/shapes/logo) tumble (`rotate + scale`), then exits to clear. Drive
it as a top-of-z-order image whose `Visible` = a `…Busy` flag; **bump a key variable in the SVG's
`<desc>` on every navigation** so the image string changes and the control reloads + replays the
animation from the start. Never depend on the timer for the actual navigation — use the platform's
built-in `Cover`/`UnCover` transition underneath, so the wipe is a flourish over a reliable nav.

**Assistant/mascot idle loops (if you have a mascot):** slow bob (`3s`), periodic wave
(`rotate` burst every few seconds), blink (`scaleY` flicker), speech-bubble cycle (bubbles fade/scale
in and out on a long loop), and a thinking indicator with staggered bouncing dots (`translateY`,
`1.2–1.8s`) plus `tin`/`tout` enter/exit.

**Loading spinner:** a ring = two stacked circles; a full track (`#d4d8db`) under an accent arc
(`stroke-dasharray`, `stroke-linecap:round`) spinning `rotate 360deg`, `1s linear infinite`.

**What the platform can't do:** there is **no per-control exit animation** — a control just vanishes
when `Visible` flips false. Cover this two ways: (a) the wipe overlay is the real exit/enter for
*page* changes; (b) within a page, right-panel swaps are instant with the *incoming* visual animating
in. Because each image re-renders when its bound data changes, **re-selecting replays that panel's
entrance** for free.

### 7. Rendering technique (data-driven SVG, Power Apps)

If the target is Power Apps / a Power BI custom visual, render every visual as a **dynamic SVG on an
Image control**:

- `Image = "data:image/svg+xml;utf8," & EncodeUrl( "<svg …>" & <interpolated values> & "</svg>" )`.
- **Single quotes** on every SVG attribute (so no `""` escaping); `EncodeUrl` round-trips the markup.
- Every Image: `ImagePosition = ImagePosition.Fit` (except full-bleed overlays = `Fill`).
- Each SVG's `viewBox` matches its rectangle's aspect ratio, so it fills with no letterboxing.
- **Integer coordinates** (`Int()`/`Round()`; delays in `ms`) — locale decimal separators can break
  SVG geometry.
- **XML-escape all human text** before interpolating: `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`, and
  **truncate** long names to fixed budgets so layouts never overflow.
- **Repeats without a gallery:** `Concat()` over a collection or inline `Table()` to draw N rows /
  podium slots / category tiles.
- **HTML chat bubbles** (if any) as an "HTML text" control: right-aligned accent bubble for the
  user, left-aligned white bordered bubble for the assistant; `white-space:pre-wrap`,
  `border-radius:14px`, `max-width:80%`.
- Build data in `Screen.OnVisible` (coerce every numeric cell with `IfError(col,0)` — blank numeric
  cells throw on read); prime state vars in `App.OnStart`.

### 8. Swap these for your brand (the ONLY values you change)

Everything else stays. To rebrand, change:

1. **Brand accent ramp** — replace the green family (`#01a982 / #006750 / #018f6e / #06372e /
   #7cf5cf / #d1ffee / #bdf5e4`) with your brand hue at the same lightness steps
   (accent / dark / deep / darkest / bright / pale-tint / soft-tint). Keep the *roles*.
2. **Brand glyph + wordmark** — the ribbon square monogram, the app name, and the subtitle.
3. **Mascot / transition motif** — swap the leaf shapes (and any mascot) for your own motif, or drop
   them; the wipe gradient + logo tile alone still reads as branded.
4. **Canvas size** — if your app isn't 1136×640, pick your own fixed size and keep all proportions
   relative to it.
5. **Category labels & count** — rename the 6 data-viz categories to yours (keep the 6-colour order;
   if you have fewer, use the first N colours).

**Do NOT change:** neutral/surface tokens, text tokens, radii, shadow recipe, the animation class
set (names/durations/easing), the stagger method, the reduced-motion guard, or the
big-number/small-label hierarchy. That invariant core is what makes it feel like this system.

### 9. My app (fill in — the re-skin target)

- **Screens & regions:** <list each screen, its ribbon, its left/right columns, galleries, overlays>
- **Data fields:** <your columns/entities and their types>
- **Metrics → cards:** <which numbers are "hero" totals, which become category tiles, which get
  pending/status chips>
- **"Mine/you" concept:** <what identity/selection state should get the accent + pale-tint + chip
  treatment>
- **Repeating lists:** <what the gallery rows represent, and how many should fit without scrolling>
- **Any mascot / assistant:** <yes/no; if yes, name + personality line>

Re-skin every screen to the system above, keep my data meaning intact, and return the styled
markup/formulas.

---
*(end of prompt)*
