# Motion redesign review (#70)

Greenfield templates, CSS and UI JavaScript with a motion layer on
[Motion](https://motion.dev) 14.5.0, vendored at
`catalog/static/catalog/vendor/motion/` (MIT, provenance in `SOURCE.txt`, no
runtime CDN, no build step). The palette, paper and sticker look, type and copy
tone are kept. URLs, form actions, methods, field names, CSRF, auth and
permissions are unchanged.

## Motion rules

- **Three springs, reused everywhere** (Bencho: consistency comes from reuse). They are
  `snappy` (0.22 s, no bounce) for highlights and press-down, `settle` (0.32 s, bounce
  0.12) for popovers and cards, and `slap` (0.34 s, bounce 0.18, LifeVal's sticker
  spring) for stamps and toasts. CSS uses `linear()` copies sampled with Motion's own
  `spring()`, so CSS hover and JS gestures feel the same.
- **Blur is a verb** (olek.si). Elements blur in and out while they move and never rest
  blurred. The amount scales with the element: 4px for rows and labels, 6px for blocks
  and cards. Large containers (a whole book, the shelf) reveal without blur, and at most
  four cards blur at once.
- **Exits are faster than entrances** (noechague.com): 0.14 s ease-out exits against
  0.3 s spring entrances.
- **Interruptible.** Motion retargets from the current value. You can reopen a menu
  mid-exit, retarget the Format thumb mid-slide, or reopen the sheet halfway out.
- Only `transform`, `opacity`, `filter` and `clip-path` animate. Hover motion runs only
  on fine pointers (`hover: hover`).

## Where each technique from the reference doc went

| Technique (source) | Where |
| --- | --- |
| Blur-in page load, 60 ms stagger, `cubic-bezier(.16,1,.3,1)` (noechague.com) | `.reveal` on headings, panels and cards (CSS, off the main thread) |
| One object travels (noechague `layoutId`) | Single highlight sliding between nav links and menu items; one yellow thumb sliding between Format options; the saved-position tick moving along the audio track |
| Sticker slap from 35% scale, 8° under (LifeVal) | Hero "Aa" sticker, login mark, "You're a member" stamp after joining, toasts |
| Prints dealt out in reading order, already at final tilt (LifeVal) | Shelf cards below the fold, dealt in on scroll 40 ms apart |
| Resting pose that straightens on hover (noechague photos) | Shelf cards and club cards rest at ±1° and straighten and lift on hover |
| Popovers grow from their trigger | Account menu, per-card menus: anchored to the trigger, `transform-origin` at its corner, spring in and quick out, Esc and click outside to close (native `[popover]`) |
| Morph, don't swap; blur masks a crossfade (Bencho, Emil Kowalski) | Play/pause icon, bookmark label, current-chapter label, pending button labels |
| Sheet curve `cubic-bezier(.32,.72,0,1)` (money.x.com, Vaul) | Table of contents sheet exit; entrance is a no-bounce spring so the edge never gaps |
| Press feedback | Motion `press()` (pointer and keyboard) on buttons, chips, menu items and cards; CSS `:active` fallback without Motion |
| Performance budget (olek.si) | Runtime audit below; per-frame work is transform-only |

## Reduced motion and no JavaScript

- `prefers-reduced-motion: reduce` turns off all transforms, blur, springs and the
  deal-in. Reveals become 0.2 s fades, popovers and the sheet fade, and the
  equaliser stops.
- With JavaScript off, every page still works:
  - Filters submit.
  - The menus and the table of contents still open, because native `[popover]` needs no script.
  - Bookmarks post and redirect.
  - Messages show as inline banners.
  - The custom deck stays hidden and the native `<audio controls>` plays.

  Browsers without `[popover]` show the menus inline.

## Verification (headless Chrome 156, local SQLite)

- `manage.py test`: 90 tests OK. Also clean: `check`, `makemigrations --check
  --dry-run`, `migrate`, `seed_demo`, `verify_demo` and `collectstatic` (debug and
  production manifest storage), in a fresh venv with `pip install --require-hashes`.
- `tests/browser_demo.py`: passes with `errors: []` and `failed_assets: []`. It covers
  keyboard, 320/390 px overflow, playback, resume and no autoplay, CSRF and nonmember
  checks, privacy, and staff report review.
- 41 extra interaction checks pass: menus (keyboard, arrows, Esc, outside click, focus
  return, reopen mid-exit), copy-link toast, Format thumb, deal-in, TOC sheet, in-place
  bookmark, deck, join stamp, comment landing, reduced motion, and no JavaScript.
  Frames are in `interactions/`.
- **Runtime motion audit.** This stands in for MotionScore: the Motion+ audit server was
  not authorised, and `npx motionscore` was not permitted in the session. Chrome Long
  Animation Frames and CDP layout counters were read while driving each animation.
  - **Forced layout: 0 ms in every scenario** (shelf and book load, nav sweep, menus,
    Format thumb, deal-in, TOC sheet, scrolling, playback).
  - Fixed along the way:
    - 55 ms and 25 ms forced reflows at load, now read from IntersectionObserver.
    - A read-after-write in the Format thumb, now measured in a ResizeObserver.
    - Per-frame text and slider writes in the deck: 164 layouts in 2.5 s down to 56,
      and the rest is the native player.

## Screenshots

`before/` and `after/` show the shelf, a book, an audiobook, a song, the clubs list, a
club and login at 1440 px and 390 px, anonymous. `after-no-js/` is the same set with
JavaScript disabled. `interactions/` holds mid-animation and settled frames.

## Known limits

- **Cross-document view transitions** (the shelf cover travelling into the book page)
  were built and then removed. In Chrome 156 they aborted intermittently, and the
  aborted transition raised an unhandled page error that no page script can catch.
- How the springs *feel* has not been judged by a person on real hardware, including
  Safari, Firefox and touch devices. The values come from the reference doc and the
  skills, not from tuning by eye.
- The native `<audio>` stays visible under the deck on purpose: it is the
  keyboard-accessible fallback and what the rehearsal drives. Some viewers may see this
  as duplicate controls.
