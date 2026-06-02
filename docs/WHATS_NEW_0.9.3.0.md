# What's new in Beam v0.9.3.0

Documentation & setup: https://github.com/MrNidnan/beam-project/#setup-and-configuration
Facebook: https://www.facebook.com/beamtheproject

This release adds live, on-the-fly display controls, a more flexible text rule,
and brings the cover-art styling and timed-mood backgrounds to the network /
browser display so it matches the native output.

---

## Live display controls: Blackout and Message

Two manual overrides sit next to the **Display** button on the main window.
They are temporary, are **not** saved, and reset to inactive on startup. Moods,
rules, player state and background rotation keep running underneath.

### Show Message
- Click **Show Message** to open a dialog, type a message and pick a duration
  (5–60 seconds, default 15).
- The message is shown centered on the preview, the projector display and the
  browser display.
- While a message is active the button changes to **Clear Message** — click it
  to remove the message early. It also clears automatically when the timer
  expires.

### Blackout
- Click **Blackout** to turn the whole output fully black (preview, projector
  and browser). The button changes to **Resume**; click it to restore the
  normal display.
- A temporary message still renders on top of a blackout, so you can black the
  screen and show a notice at the same time.

### Status bar
The bottom status bar now reports the live state in one line:

```
Player: <state> | Mood: <mood> | Display: ON/OFF/BLACKOUT | [Message: Ns |] Network: ON/OFF
```

The `Message: Ns` segment only appears while a temporary message is counting
down.

---

## Cut / Trim rule works on any tag

The old "Trim () in Title" rule is now **Cut / Trim** and can be applied to any
input ID3 tag, not just the title.

- In the rule editor choose **Cut / Trim**, pick the **Input ID3 tag**, and set
  **Start from** — the symbol (or text) where trimming begins. It can be a
  single character such as `(` or `-`, or a longer string.
- Examples:
  - Start from `(` turns `Title (Live)` into `Title`.
  - Start from `-` turns `Title - Live` into `Title`.
- Existing "Trim () in Title" rules migrate to the new type automatically on
  load.
- Trimming is also applied to the previous-song display, so it no longer shows
  the untrimmed value.

---

## Mood backgrounds: Keep existing + Readability

The mood editor's **Background** section is now a single **Background type**
dropdown with only the relevant controls shown:

- **Keep existing** — leaves whatever background is already on screen. Useful
  for timed message moods (e.g. `LAST TANDA`) that should overlay text without
  swapping the background.
- **Color** — a single uniform background color.
- **Single image** — one background image.
- **Image slideshow** — a rotating folder of images; the rotation interval and
  random-order options now live inside this type.

When **Keep existing** is selected a **Readability** slider (0–100) applies a
combined blur + dark overlay to the current background so on-screen text is
easier to read (0 = no change, 100 = strong blur and darkening).

Typical use:
1. Set up the default mood slideshow images with no text.
2. Add a mood with the text you want and a duration (X seconds).
3. Set its background to **Keep existing** and raise **Readability** to blur and
   darken the background behind the text.

Works on both the native (wx) and network / browser displays. Old mood
configurations load unchanged.

---

## Cover-art Advanced display options on the browser display

The cover-art tweaks in **Advanced display options** (corner radius, outline
enable / alpha / width) now also apply to the network / browser display and
update live, matching the native render. The browser cover art preserves its
aspect ratio (letterbox) instead of being cropped to a square.

- Outline width can now be set up to 32 px.
- Changing these options is reflected immediately on the preview, projector and
  browser without reopening the preferences window, and is saved automatically.
- Note: the soft "feather" edge of the native render is approximated by corner
  rounding in the browser.

---

## Other fixes

- Network display enable/disable now actually starts and stops the service, and
  start/stop is more robust across Windows, Linux and macOS.
- Background / opacity alignment between the web display and the native display.
- Rotating backgrounds refresh reliably.
- Windows iTunes: more robust COM connection on frozen builds, with a clearer
  log message when the iTunes COM server cannot start (e.g. the Microsoft Store
  version of iTunes, which has no COM support).
- Various cosmetic fixes on Windows and Linux (no bold section headers on GTK,
  checkbox layout, field help shown as tooltips).
</content>
</invoke>
