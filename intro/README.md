# Hallucinated Games — Studio Intro

The "Nintendo Presents" moment for our games. The logo **hallucinates itself out
of noise**: the screen starts as pure static, a particle field denoises into the
wordmark, the chromatic split collapses, a glitch snaps it into lock, and the
tagline lands. About 4.6 seconds.

It's a canvas animation, not a video file — it renders live in the browser at
whatever resolution the game is running, stays sharp on a 4K monitor, and costs
~22 KB instead of a multi‑megabyte download.

| | |
|---|---|
| **Preview / tune it** | open `intro/index.html` |
| **The whole thing** | `intro/hallucinated-intro.js` (no dependencies) |
| **Video export** | `intro/video/hallucinated-intro.mp4` (1080p30, H.264 + AAC) |

---

## Add it to a game

Recommended — point at the copy on the hub so every game updates at once:

```html
<script src="https://www.hallucinatedgames.com/intro/hallucinated-intro.js"></script>
<script>
  HallucinatedIntro.play({ sound: true }).then(startGame);
</script>
```

Or drop `hallucinated-intro.js` next to the game and use a relative path, which
also works offline.

Called with no `canvas`, it builds its own fullscreen black overlay, plays,
removes itself, and resolves — so `startGame()` runs on a clean page. If the game
already has a loading screen, hand it a canvas instead:

```js
HallucinatedIntro.play({ canvas: document.getElementById('loader') })
  .then(startGame);
```

### Options

| Option | Default | What it does |
|---|---|---|
| `canvas` | — | Draw into an existing canvas instead of a fullscreen overlay |
| `skippable` | `true` | Click, tap or any key ends it early |
| `sound` | `false` | Procedural WebAudio sting — riser, impact, shimmer chord |
| `tagline` | `100% VIBE CODED · 0% UNIT TESTED` | Text under the mark; `''` hides it |
| `quality` | `'high'` | `'low'` drops the static field and thins the particles |
| `onSkip` | — | Called if the viewer skipped |

The promise resolves with `{ skipped: true|false }` either way, so the game boots
whether or not anyone sat through it.

### Things it already handles

- **Sound is off unless you ask.** Browsers block autoplay audio without a user
  gesture, so `sound: true` belongs on a click ("Press Start"), not on page load.
- **`prefers-reduced-motion`** — holds the finished logo for 1.6s instead of
  strobing, rather than flashing at someone who asked it not to.
- **Any aspect ratio** — authored at 1920×1080 and letterboxed to fit, so phones
  and ultrawides both get the full lockup.
- **Slow or offline font CDN** — waits up to 1.5s for Orbitron, then falls back
  to Arial Black and plays anyway.
- **Performance** — ~5ms per frame at full 1080p, well inside a 60fps budget.
  The scene is built before the clock starts so frame one isn't a hitch.

---

## Re-rendering the video

Only needed if you change the animation and want the `.mp4` to match. The
animation is deterministic — `renderFrame(ctx, t, w, h)` draws identical pixels
for a given `t` — so frames are captured from a real browser rather than
re-implemented.

```bash
# 1. audio
python intro/tools/make-sting.py sting.wav

# 2. frames — start the catcher, then open the render page in a browser
python intro/tools/frame-server.py . frames/ 8792
#    http://localhost:8792/intro/tools/render-frames.html?fps=30&scale=1

# 3. mux
ffmpeg -y -framerate 30 -i frames/frame_%05d.png -i sting.wav \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 160k -shortest intro/video/hallucinated-intro.mp4
```

`make-sting.py` is the offline twin of `playSting()` in the JS — same riser, same
impact at the 2.30s lock, same chord — so the exported video matches what a game
plays live.

The mp4 is for YouTube, itch.io and socials. **For the games themselves, use the
JS** — it's a fraction of the size and renders at native resolution.
