const layoutCanvasEl = document.getElementById("layout-canvas");
const emptyStateEl = document.getElementById("empty-state");
const textMeasurerEl = document.getElementById("text-measurer");
const blackoutLayerEl = document.getElementById("blackout-layer");
const tempMessageOverlayEl = document.getElementById("temp-message-overlay");
const tempMessagePanelEl = document.getElementById("temp-message-panel");

const COVER_ART_URL = "/media/cover-art/current";
const ABSOLUTE_MIN_TEXT_SIZE_PX = 10;
const ABSOLUTE_MAX_TEXT_SIZE_PX = 420;
const DEFAULT_CENTER_MAX_WIDTH_PERCENT = 85;
// Text must keep at least a 5% margin at the top and bottom of the screen
// (kept in sync with the native display's VERTICAL_SAFE_*_RATIO constants).
const VERTICAL_SAFE_TOP_RATIO = 0.05;
const VERTICAL_SAFE_BOTTOM_RATIO = 0.95;
const BLOCK_FIT_MAX_ITERATIONS = 60;
const GENERIC_FONT_FAMILIES = new Set([
  "serif",
  "sans-serif",
  "monospace",
  "cursive",
  "fantasy",
  "system-ui",
  "ui-serif",
  "ui-sans-serif",
  "ui-monospace",
  "math",
  "emoji",
  "fangsong",
]);

let screenWakeLock = null;
let wakeLockBound = false;
let reconnectDelayMs = 1000;
let reconnectTimer = null;
let activeSocket = null;
let lastSnapshot = null;
let lastSequence = 0;
let lastBackgroundRenderKey = "";

// Media is loaded into in-memory blob object URLs and only re-fetched when the
// content identity changes, so an unchanged song/mood never reloads (no blink)
// and a real change swaps in a pre-decoded image instantly (direct, no fade).
let coverArtElement = null;
let coverArtIdentity = "";
let coverArtObjectUrl = "";
const backgroundObjectUrls = {
  "--beam-background-base": "",
  "--beam-background-overlay": "",
};

function clearReconnectTimer() {
  if (reconnectTimer !== null) {
    globalThis.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function scheduleReconnect() {
  clearReconnectTimer();
  reconnectTimer = globalThis.setTimeout(() => {
    reconnectTimer = null;
    connectEvents();
  }, reconnectDelayMs);
  reconnectDelayMs = Math.min(reconnectDelayMs * 2, 15000);
}

async function enterFullscreen() {
  if (document.fullscreenElement) {
    return;
  }

  try {
    await document.documentElement.requestFullscreen?.();
  } catch {
    // Ignore fullscreen failures. Wake lock still helps when fullscreen is blocked.
  }
}

async function requestWakeLock() {
  if (!navigator.wakeLock?.request || document.visibilityState !== "visible") {
    return;
  }

  try {
    if (screenWakeLock?.released === false) {
      return;
    }

    screenWakeLock = await navigator.wakeLock.request("screen");

    if (!wakeLockBound) {
      wakeLockBound = true;
      screenWakeLock.addEventListener("release", () => {});
    }
  } catch {}
}

async function activateDisplayMode() {
  await enterFullscreen();
  await requestWakeLock();
}

function installDisplayActivationHandlers() {
  const activate = async () => {
    await activateDisplayMode();
  };

  document.addEventListener("click", activate);
  document.addEventListener("touchstart", activate, { passive: true });

  document.addEventListener("visibilitychange", async () => {
    if (document.visibilityState === "visible") {
      await requestWakeLock();
      if (activeSocket === null || activeSocket.readyState > WebSocket.OPEN) {
        connectEvents();
      }
    }
  });
}

function normalizeGenre(song) {
  const isCortina = String(song?.isCortina || "")
    .trim()
    .toLowerCase();
  if (isCortina === "yes") {
    return "";
  }

  const genre = (song?.genre || "").trim().toLowerCase();
  if (genre.includes("milonga")) {
    return "milonga";
  }
  if (genre.includes("vals") || genre.includes("waltz")) {
    return "vals";
  }
  if (genre.includes("tango")) {
    return "tango";
  }
  return "";
}

function hasEnabledMoodTheme(snapshot, themeName) {
  const normalizedThemeName = String(themeName || "")
    .trim()
    .toLowerCase();
  if (!normalizedThemeName) {
    return false;
  }

  const enabledMoodNames = Array.isArray(snapshot?.enabledMoodNames)
    ? snapshot.enabledMoodNames
    : [];

  return enabledMoodNames.some(
    (moodName) =>
      String(moodName || "")
        .trim()
        .toLowerCase() === normalizedThemeName,
  );
}

function formatSongDate(song) {
  const year = String(song?.year || "").trim();
  return year;
}

function formatPreviousSong(song) {
  const title = String(song?.title || "").trim();
  if (!title) {
    return "";
  }

  return `Previous song: ${title}`;
}

function normalizeTextFlow(textFlow) {
  const normalizedTextFlow = String(textFlow || "")
    .trim()
    .toLowerCase();
  if (normalizedTextFlow === "cut") {
    return "cut";
  }
  if (normalizedTextFlow === "scale") {
    return "scale";
  }
  return "wrap";
}

function normalizeAlignment(alignment) {
  const normalizedAlignment = String(alignment || "")
    .trim()
    .toLowerCase();
  if (normalizedAlignment === "left") {
    return "left";
  }
  if (normalizedAlignment === "right") {
    return "right";
  }
  return "center";
}

function normalizeWeight(weight) {
  const normalizedWeight = String(weight || "")
    .trim()
    .toLowerCase();
  return normalizedWeight === "bold" ? "700" : "400";
}

function normalizeStyle(style) {
  const normalizedStyle = String(style || "")
    .trim()
    .toLowerCase();
  return normalizedStyle === "italic" ? "italic" : "normal";
}

function parseFontColor(fontColor) {
  const matchedValues = String(fontColor || "")
    .match(/\d+(?:\.\d+)?/g)
    ?.map(Number);

  if (!matchedValues || matchedValues.length < 3) {
    return "rgba(255, 249, 244, 1)";
  }

  const [red, green, blue, alpha = 255] = matchedValues;
  return `rgba(${red}, ${green}, ${blue}, ${Math.max(0, Math.min(1, alpha / 255))})`;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function isItemActive(item) {
  return (
    String(item?.active || "yes")
      .trim()
      .toLowerCase() === "yes"
  );
}

function getDisplayItems(snapshot) {
  return Array.isArray(snapshot?.displayItems) ? snapshot.displayItems : [];
}

function buildFallbackDisplayItems(snapshot) {
  const fallbackItems = [];
  const primaryText =
    String(snapshot?.currentSong?.title || "").trim() || "Waiting for Beam";
  const artistText = String(
    snapshot?.currentSong?.artist || snapshot?.moodName || "",
  ).trim();
  const yearText = formatSongDate(snapshot?.currentSong);
  const previousSongText = formatPreviousSong(snapshot?.previousSong);

  if (artistText) {
    fallbackItems.push({
      field: "%Artist",
      text: artistText,
      active: "yes",
      alignment: "Center",
      font: "Palatino Linotype",
      fontColor: "(255, 215, 186, 255)",
      size: 8,
      style: "Normal",
      weight: "Normal",
      position: [18, 50],
      textFlow: "Wrap",
    });
  }

  fallbackItems.push({
    field: "%Title",
    text: primaryText,
    active: "yes",
    alignment: "Center",
    font: "Palatino Linotype",
    fontColor: "(255, 249, 244, 255)",
    size: 14,
    style: "Normal",
    weight: "Bold",
    position: [36, 50],
    textFlow: "Scale",
  });

  if (yearText) {
    fallbackItems.push({
      field: "%Year",
      text: yearText,
      active: "yes",
      alignment: "Center",
      font: "Palatino Linotype",
      fontColor: "(255, 243, 234, 220)",
      size: 6,
      style: "Normal",
      weight: "Normal",
      position: [58, 50],
      textFlow: "Cut",
    });
  }

  if (previousSongText) {
    fallbackItems.push({
      field: "%PreviousSong",
      text: previousSongText,
      active: "yes",
      alignment: "Left",
      font: "Palatino Linotype",
      fontColor: "(255, 249, 244, 255)",
      size: 4,
      style: "Normal",
      weight: "Normal",
      position: [90, 4],
      textFlow: "Cut",
    });
  }

  return fallbackItems;
}

function getBaseItemFontSizePx(item, canvasHeight) {
  return Math.max(
    ABSOLUTE_MIN_TEXT_SIZE_PX,
    Math.round((Number(item.size || 0) / 100) * canvasHeight),
  );
}

function getItemFontSizePx(item, canvasHeight) {
  return Math.min(
    ABSOLUTE_MAX_TEXT_SIZE_PX,
    getBaseItemFontSizePx(item, canvasHeight),
  );
}

function quoteFontFamily(fontFamily) {
  const normalizedFontFamily = String(fontFamily || "").trim();
  if (!normalizedFontFamily) {
    return "";
  }

  const lowerCaseFontFamily = normalizedFontFamily.toLowerCase();
  if (
    GENERIC_FONT_FAMILIES.has(lowerCaseFontFamily) ||
    (normalizedFontFamily.startsWith('"') &&
      normalizedFontFamily.endsWith('"')) ||
    (normalizedFontFamily.startsWith("'") && normalizedFontFamily.endsWith("'"))
  ) {
    return normalizedFontFamily;
  }

  return JSON.stringify(normalizedFontFamily);
}

function getFontFamily(item) {
  const fontFace = String(item.font || "").trim();
  if (!fontFace) {
    return '"Liberation Sans", Arial, sans-serif';
  }

  return `${quoteFontFamily(fontFace)}, "Liberation Sans", Arial, sans-serif`;
}

function configureTextMeasurer(item, fontSizePx, options = {}) {
  const {
    maxWidthPx,
    lineHeight = "normal",
    preserveLineBreaks = false,
    allowWrap = false,
  } = options;

  textMeasurerEl.className = `text-measurer layout-item align-${normalizeAlignment(
    item.alignment,
  )} flow-${normalizeTextFlow(item.textFlow)}`;
  textMeasurerEl.style.width = Number.isFinite(maxWidthPx)
    ? `${Math.max(0, maxWidthPx)}px`
    : "auto";
  textMeasurerEl.style.fontFamily = getFontFamily(item);
  // Measure at the exact size that will render, or wrapping decisions made
  // below the old 10px clamp would disagree with the drawn text.
  textMeasurerEl.style.fontSize = `${Math.max(1, fontSizePx)}px`;
  textMeasurerEl.style.fontStyle = normalizeStyle(item.style);
  textMeasurerEl.style.fontWeight = normalizeWeight(item.weight);
  textMeasurerEl.style.lineHeight = lineHeight;
  textMeasurerEl.style.whiteSpace = preserveLineBreaks ? "pre-wrap" : "pre";
  textMeasurerEl.style.overflowWrap = allowWrap ? "anywhere" : "normal";
}

function measureTextElement(text, item, fontSizePx, options = {}) {
  configureTextMeasurer(item, fontSizePx, options);
  textMeasurerEl.textContent = text;

  const rect = textMeasurerEl.getBoundingClientRect();
  return {
    width: rect.width,
    height: rect.height,
  };
}

function measureSingleLineText(text, item, fontSizePx) {
  return measureTextElement(text, item, fontSizePx);
}

function getMeasuredLineSpacing(item, fontSizePx) {
  const lineHeightPx = measureSingleLineText("Ag", item, fontSizePx).height;
  return {
    lineHeightPx,
    lineSpacingPx: Math.max(lineHeightPx, Math.floor(lineHeightPx * 1.1)),
  };
}

function trimCutText(text, item, maxWidthPx, fontSizePx) {
  let nextText = String(text);
  let measuredWidth = measureSingleLineText(nextText, item, fontSizePx).width;
  if (measuredWidth <= maxWidthPx) {
    return nextText;
  }

  while (nextText && measuredWidth > maxWidthPx) {
    nextText = nextText.slice(0, -1);
    measuredWidth = measureSingleLineText(nextText, item, fontSizePx).width;
  }

  let ellipsisText = `${nextText.slice(0, Math.max(0, nextText.length - 2))}...`;
  while (
    ellipsisText.length > 3 &&
    measureSingleLineText(ellipsisText, item, fontSizePx).width > maxWidthPx
  ) {
    ellipsisText = `${ellipsisText.slice(0, -4)}...`;
  }

  return ellipsisText;
}

function wrapLongToken(token, item, fontSizePx, maxWidthPx) {
  if (!token) {
    return [""];
  }

  const wrappedParts = [];
  let remaining = token;

  while (remaining) {
    // Binary search for the longest prefix that still fits (prefix width
    // grows monotonically with its length). Always take at least one char
    // so a too-narrow box cannot loop forever.
    let low = 1;
    let high = remaining.length;
    let splitIndex = 0;
    while (low <= high) {
      const mid = (low + high) >> 1;
      const candidateWidth = measureSingleLineText(
        remaining.slice(0, mid),
        item,
        fontSizePx,
      ).width;
      if (candidateWidth <= maxWidthPx) {
        splitIndex = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    if (splitIndex <= 0) {
      splitIndex = 1;
    }

    wrappedParts.push(remaining.slice(0, splitIndex));
    remaining = remaining.slice(splitIndex);
  }

  return wrappedParts;
}

function wrapTextLines(text, item, fontSizePx, maxWidthPx) {
  if (maxWidthPx <= 0) {
    return [text];
  }

  const wrappedLines = [];
  const paragraphs = String(text).split(/\r?\n/);

  (paragraphs.length ? paragraphs : [""]).forEach((paragraph) => {
    const words = paragraph.split(/\s+/).filter(Boolean);
    if (!words.length) {
      wrappedLines.push("");
      return;
    }

    let currentLine = "";
    words.forEach((word) => {
      const candidate = currentLine ? `${currentLine} ${word}` : word;
      const candidateWidth = measureSingleLineText(
        candidate,
        item,
        fontSizePx,
      ).width;

      if (candidateWidth <= maxWidthPx) {
        currentLine = candidate;
        return;
      }

      if (currentLine) {
        wrappedLines.push(currentLine);
        currentLine = "";
      }

      const wordWidth = measureSingleLineText(word, item, fontSizePx).width;
      if (wordWidth <= maxWidthPx) {
        currentLine = word;
        return;
      }

      const wrappedWordParts = wrapLongToken(
        word,
        item,
        fontSizePx,
        maxWidthPx,
      );
      wrappedLines.push(...wrappedWordParts.slice(0, -1));
      currentLine = wrappedWordParts.at(-1) || "";
    });

    if (currentLine || !wrappedLines.length) {
      wrappedLines.push(currentLine);
    }
  });

  return wrappedLines.length ? wrappedLines : [""];
}

function getItemMaxWidth(canvasWidth, item, alignment) {
  const maxWidthPercent = Number(item?.maxWidthPercent ?? 0);
  if (maxWidthPercent > 0) {
    return Math.max(0, (maxWidthPercent / 100) * canvasWidth);
  }
  const positionX = Number(item?.position?.[1] ?? 0);
  if (alignment === "center") {
    return (DEFAULT_CENTER_MAX_WIDTH_PERCENT / 100) * canvasWidth;
  }
  return Math.max(0, ((100 - positionX) / 100) * canvasWidth);
}

function resolveFitSettings(item, baseFontSizePx, canvasHeight) {
  const adaptive = String(item?.adaptiveSize ?? "yes") !== "no";
  const minSizeSetting = Number(item?.minSize ?? 0);
  // Floor at 1px like the native display so both displays shrink identically.
  const minFontPx = Math.max(
    1,
    minSizeSetting > 0
      ? Math.round((minSizeSetting / 100) * canvasHeight)
      : Math.round(baseFontSizePx * 0.75),
  );
  return {
    adaptive,
    minFontPx: Math.min(minFontPx, baseFontSizePx),
    maxLines: Math.max(0, Number(item?.maxLines ?? 0) || 0),
  };
}

function applyHorizontalPosition(element, alignment, item, canvasWidth) {
  const positionX = Number(item?.position?.[1] ?? 0);
  element.classList.add(`align-${alignment}`);

  if (alignment === "center") {
    element.style.transform = "translateX(-50%)";
    element.style.left = `${canvasWidth / 2}px`;
    element.style.right = "auto";
    return;
  }

  element.style.transform = "none";
  if (alignment === "right") {
    element.style.right = `${(positionX / 100) * canvasWidth}px`;
    element.style.left = "auto";
    return;
  }

  element.style.left = `${(positionX / 100) * canvasWidth}px`;
  element.style.right = "auto";
}

// A song change only changes the cover-art *image*, not its slot. The element is
// reused across renders and its bitmap is only re-fetched when the identity
// changes, so unrelated snapshots (status, playlist) never reload it (no blink).
function coverArtIdentityKey(snapshot) {
  const coverArt = snapshot.coverArt || {};
  return String(
    coverArt.sourcePath ||
      snapshot.currentSong?.filePath ||
      snapshot.currentSong?.title ||
      "",
  );
}

function removeCoverArt() {
  if (coverArtElement) {
    coverArtElement.remove();
    coverArtElement.removeAttribute("src");
  }
  coverArtIdentity = "";
  if (coverArtObjectUrl) {
    URL.revokeObjectURL(coverArtObjectUrl);
    coverArtObjectUrl = "";
  }
}

async function loadCoverArtImage(url, identity) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`cover art request failed: ${response.status}`);
    }
    const objectUrl = URL.createObjectURL(await response.blob());
    const decoder = new Image();
    decoder.src = objectUrl;
    if (typeof decoder.decode === "function") {
      await decoder.decode().catch(() => {});
    }
    // Drop stale loads: the song may have changed again while fetching.
    if (identity !== coverArtIdentity || !coverArtElement) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    coverArtElement.src = objectUrl;
    const previousObjectUrl = coverArtObjectUrl;
    coverArtObjectUrl = objectUrl;
    if (previousObjectUrl) {
      URL.revokeObjectURL(previousObjectUrl);
    }
  } catch {
    // Fall back to the direct URL so something shows if the blob load fails.
    if (identity === coverArtIdentity && coverArtElement) {
      coverArtElement.src = url;
    }
  }
}

function updateCoverArt(item, snapshot, canvasWidth, canvasHeight) {
  const coverArt = snapshot.coverArt || {};
  const isAvailable = Boolean(coverArt.available ?? snapshot.coverArtAvailable);
  if (!item || !isAvailable) {
    removeCoverArt();
    return;
  }

  if (!coverArtElement) {
    coverArtElement = document.createElement("img");
  }

  const alignment = normalizeAlignment(item.alignment);
  const sizePx = Math.max(
    48,
    Math.round((Number(item.size || 0) / 100) * canvasHeight),
  );
  const topPx = Math.round(
    (Number(item?.position?.[0] ?? 0) / 100) * canvasHeight,
  );

  coverArtElement.className = `layout-cover-art align-${alignment}`;
  coverArtElement.alt = snapshot.currentSong?.title
    ? `${snapshot.currentSong.title} cover art`
    : "Current cover art";
  coverArtElement.width = sizePx;
  coverArtElement.height = sizePx;
  coverArtElement.style.top = `${topPx}px`;
  coverArtElement.style.width = `${sizePx}px`;
  coverArtElement.style.height = `${sizePx}px`;
  applyCoverArtStyle(coverArtElement, snapshot.coverArtStyle || {}, sizePx);
  applyHorizontalPosition(coverArtElement, alignment, item, canvasWidth);
  if (!coverArtElement.isConnected) {
    layoutCanvasEl.append(coverArtElement);
  }

  // Only (re)fetch the bitmap when the cover art identity actually changes.
  const identity = coverArtIdentityKey(snapshot);
  if (identity === coverArtIdentity && coverArtObjectUrl) {
    return;
  }
  coverArtIdentity = identity;
  const url = `${coverArt.url || COVER_ART_URL}?v=${encodeURIComponent(identity)}`;
  loadCoverArtImage(url, identity);
}

// Mirror the native (wx) cover-art tweaks from Advanced display options so the
// browser display matches: aspect-preserving fit, configurable corner radius,
// and optional white outline (alpha 0-255, width in px). Inline styles override
// the decorative defaults in app.css.
function applyCoverArtStyle(coverArtEl, style, sizePx) {
  // Native scales with min(w/iw, h/ih) -> letterbox, i.e. CSS "contain".
  coverArtEl.style.objectFit = "contain";
  coverArtEl.style.background = "transparent";

  const cornerRadius = style.cornerRadius;
  let radiusPx;
  if (
    cornerRadius === undefined ||
    cornerRadius === null ||
    String(cornerRadius).toLowerCase() === "auto"
  ) {
    radiusPx = Math.round(sizePx * 0.08);
  } else {
    radiusPx = Math.max(
      0,
      Math.min(Number(cornerRadius) || 0, Math.floor(sizePx / 2)),
    );
  }
  coverArtEl.style.borderRadius = `${radiusPx}px`;
  coverArtEl.style.border = "none";

  const outlineWidth = Math.max(0, Number(style.outlineWidth) || 0);
  const outlineAlpha = Math.max(0, Math.min(255, Number(style.outlineAlpha) || 0));
  if (style.outlineEnabled && outlineWidth > 0 && outlineAlpha > 0) {
    const alpha = (outlineAlpha / 255).toFixed(3);
    coverArtEl.style.boxShadow = `0 0 0 ${outlineWidth}px rgba(255, 255, 255, ${alpha})`;
  } else {
    coverArtEl.style.boxShadow = "none";
  }
}

function layoutTextItem(item, text, canvasWidth, canvasHeight, overrides = {}) {
  const alignment = normalizeAlignment(item.alignment);
  const textFlow = normalizeTextFlow(item.textFlow);
  let fontSizePx = getItemFontSizePx(item, canvasHeight);
  // Resolve the minimum from the configured size before applying any forced
  // cap, so repeated block-fit steps cannot drag the minimum down with them.
  const fitSettings = resolveFitSettings(item, fontSizePx, canvasHeight);
  if (Number.isFinite(overrides.forcedFontPx)) {
    fontSizePx = Math.max(
      1,
      Math.min(fontSizePx, Math.floor(overrides.forcedFontPx)),
    );
  }
  const { adaptive } = fitSettings;
  const minFontPx = Math.min(fitSettings.minFontPx, fontSizePx);
  const maxLines = Number.isFinite(overrides.forcedMaxLines)
    ? overrides.forcedMaxLines
    : fitSettings.maxLines;
  const maxWidthPx = getItemMaxWidth(canvasWidth, item, alignment);
  let renderedText = text;
  let wrappedLineCount = 1;

  if (textFlow === "scale") {
    let measurement = measureSingleLineText(text, item, fontSizePx);
    while (fontSizePx > minFontPx && measurement.width > maxWidthPx * 0.95) {
      fontSizePx = Math.max(minFontPx, Math.floor(fontSizePx * 0.92));
      measurement = measureSingleLineText(text, item, fontSizePx);
    }
    if (measurement.width > maxWidthPx) {
      renderedText = trimCutText(text, item, maxWidthPx, fontSizePx);
    }
  }

  if (textFlow === "cut") {
    if (adaptive) {
      while (
        fontSizePx > minFontPx &&
        measureSingleLineText(text, item, fontSizePx).width > maxWidthPx
      ) {
        fontSizePx = Math.max(minFontPx, Math.floor(fontSizePx * 0.92));
      }
    }
    renderedText = trimCutText(text, item, maxWidthPx, fontSizePx);
  }

  if (textFlow === "wrap") {
    let wrappedLines = wrapTextLines(text, item, fontSizePx, maxWidthPx);
    if (maxLines > 0 && wrappedLines.length > maxLines) {
      if (adaptive) {
        while (fontSizePx > minFontPx && wrappedLines.length > maxLines) {
          fontSizePx = Math.max(minFontPx, Math.floor(fontSizePx * 0.92));
          wrappedLines = wrapTextLines(text, item, fontSizePx, maxWidthPx);
        }
      }
      if (wrappedLines.length > maxLines) {
        const lastLine = wrappedLines
          .slice(maxLines - 1)
          .filter(Boolean)
          .join(" ");
        wrappedLines = wrappedLines
          .slice(0, maxLines - 1)
          .concat(trimCutText(lastLine, item, maxWidthPx, fontSizePx));
      }
    }
    renderedText = wrappedLines.join("\n");
    wrappedLineCount = wrappedLines.length;
  }

  const { lineHeightPx, lineSpacingPx } = getMeasuredLineSpacing(
    item,
    fontSizePx,
  );
  const effectiveLineSpacingPx = overrides.tightSpacing
    ? lineHeightPx
    : lineSpacingPx;
  const extraHeightPx = Math.max(
    0,
    (wrappedLineCount - 1) * effectiveLineSpacingPx,
  );
  // Text keeps at least the top safe margin regardless of the configured
  // vertical position (mirrors the native display's VERTICAL_SAFE_TOP_RATIO).
  const topPx = Math.max(
    Math.round((Number(item?.position?.[0] ?? 0) / 100) * canvasHeight),
    Math.round(canvasHeight * VERTICAL_SAFE_TOP_RATIO),
  );

  return {
    item,
    text,
    alignment,
    textFlow,
    renderedText,
    wrappedLineCount,
    fontSizePx,
    minFontPx,
    adaptive,
    maxWidthPx,
    lineHeightPx,
    lineSpacingPx: effectiveLineSpacingPx,
    extraHeightPx,
    topPx,
    totalHeightPx: lineHeightPx + extraHeightPx,
  };
}

function buildTextItemElement(layout, canvasWidth, extraVerticalOffset) {
  const { item, alignment, textFlow } = layout;
  const itemEl = document.createElement("p");

  itemEl.className = `layout-item align-${alignment} flow-${textFlow}`;
  itemEl.dataset.field = String(item.field || "").replaceAll("%", "") || "text";
  itemEl.innerHTML = escapeHtml(layout.renderedText).replaceAll("\n", "<br>");
  itemEl.style.top = `${layout.topPx + extraVerticalOffset}px`;
  itemEl.style.color = parseFontColor(item.fontColor);
  itemEl.style.fontFamily = getFontFamily(item);
  itemEl.style.fontSize = `${layout.fontSizePx}px`;
  itemEl.style.fontStyle = normalizeStyle(item.style);
  itemEl.style.fontWeight = normalizeWeight(item.weight);
  itemEl.style.width = `${Math.max(0, layout.maxWidthPx)}px`;
  itemEl.style.lineHeight =
    textFlow === "wrap"
      ? `${layout.lineSpacingPx}px`
      : `${layout.lineHeightPx}px`;

  applyHorizontalPosition(itemEl, alignment, item, canvasWidth);

  return itemEl;
}

// Cumulative vertical offsets replicating the native reflow rules: items in
// the same Position row reserve the tallest extra height in that row; later
// rows are pushed down by the accumulated total.
function computeRowOffsets(layouts) {
  const offsets = [];
  let cumulativeVerticalOffset = 0;
  let currentRowPosition = null;
  let currentRowExtraHeight = 0;

  layouts.forEach((layout) => {
    const rowPosition = Number(layout.item?.position?.[0] ?? 0);
    if (currentRowPosition === null) {
      currentRowPosition = rowPosition;
    } else if (rowPosition > currentRowPosition) {
      cumulativeVerticalOffset += currentRowExtraHeight;
      currentRowExtraHeight = 0;
      currentRowPosition = rowPosition;
    }

    offsets.push(cumulativeVerticalOffset);
    currentRowExtraHeight = Math.max(
      currentRowExtraHeight,
      layout.extraHeightPx,
    );
  });

  return offsets;
}

function blockOverflowPx(layouts, safeBottom) {
  const offsets = computeRowOffsets(layouts);
  let worst = 0;
  layouts.forEach((layout, index) => {
    if (!String(layout.renderedText || "").trim()) {
      return;
    }
    const bottom = layout.topPx + offsets[index] + layout.totalHeightPx;
    worst = Math.max(worst, bottom - safeBottom);
  });
  return worst;
}

// Shrink the centered text block until it fits the vertical safe area,
// mirroring the native display's staged strategy: font size first, then
// tighter line spacing, then fewer lines on non-title items, then fewer
// lines on the title itself.
function fitLayoutsVertically(layouts, canvasWidth, canvasHeight) {
  const safeBottom = Math.round(canvasHeight * VERTICAL_SAFE_BOTTOM_RATIO);
  if (blockOverflowPx(layouts, safeBottom) <= 0) {
    return layouts;
  }

  const candidateIndexes = layouts
    .map((layout, index) => ({ layout, index }))
    .filter(
      ({ layout }) =>
        layout.alignment === "center" &&
        layout.adaptive &&
        String(layout.renderedText || "").trim(),
    )
    .map(({ index }) => index);
  if (!candidateIndexes.length) {
    return layouts;
  }

  // Multi-line (title-like) items shrink first, largest font first.
  candidateIndexes.sort((leftIndex, rightIndex) => {
    const leftMultiLine = layouts[leftIndex].wrappedLineCount > 1 ? 0 : 1;
    const rightMultiLine = layouts[rightIndex].wrappedLineCount > 1 ? 0 : 1;
    if (leftMultiLine !== rightMultiLine) {
      return leftMultiLine - rightMultiLine;
    }
    return layouts[rightIndex].fontSizePx - layouts[leftIndex].fontSizePx;
  });
  const titleIndex = candidateIndexes[0];

  const overrides = new Map(candidateIndexes.map((index) => [index, {}]));
  const relayout = (index) => {
    layouts[index] = layoutTextItem(
      layouts[index].item,
      layouts[index].text,
      canvasWidth,
      canvasHeight,
      overrides.get(index),
    );
  };

  for (let step = 0; step < BLOCK_FIT_MAX_ITERATIONS; step += 1) {
    if (blockOverflowPx(layouts, safeBottom) <= 0) {
      return layouts;
    }

    // Stage 1: step the first candidate still above its minimum size.
    const target = candidateIndexes.find(
      (index) => layouts[index].fontSizePx > layouts[index].minFontPx,
    );
    if (target !== undefined) {
      overrides.get(target).forcedFontPx = Math.max(
        layouts[target].minFontPx,
        Math.floor(layouts[target].fontSizePx * 0.92),
      );
      relayout(target);
      continue;
    }

    // Stage 2: tighten line spacing on wrapped centered items.
    let tightened = false;
    candidateIndexes.forEach((index) => {
      if (
        !overrides.get(index).tightSpacing &&
        layouts[index].wrappedLineCount > 1
      ) {
        overrides.get(index).tightSpacing = true;
        relayout(index);
        tightened = true;
      }
    });
    if (tightened) {
      continue;
    }

    // Stage 3: force non-title candidates to a single trimmed line.
    let forced = false;
    candidateIndexes.forEach((index) => {
      if (
        index !== titleIndex &&
        layouts[index].wrappedLineCount > 1 &&
        overrides.get(index).forcedMaxLines !== 1
      ) {
        overrides.get(index).forcedMaxLines = 1;
        relayout(index);
        forced = true;
      }
    });
    if (forced) {
      continue;
    }

    // Stage 4: reduce the title's line count one line at a time.
    const titleLines = layouts[titleIndex].wrappedLineCount;
    if (titleLines > 1) {
      overrides.get(titleIndex).forcedMaxLines = titleLines - 1;
      relayout(titleIndex);
      continue;
    }

    break;
  }

  return layouts;
}

function getRenderableItems(snapshot) {
  // Any layout at all (even with every item inactive or hidden) means a mood
  // is in charge of the screen: render exactly what it says, like the native
  // display. The fallback layout only covers a snapshot with no layout items
  // (server idle / no display data yet).
  const displayItems = getDisplayItems(snapshot);
  if (displayItems.length > 0) {
    return displayItems.filter((item) => isItemActive(item));
  }
  return buildFallbackDisplayItems(snapshot);
}

function renderLayout(snapshot) {
  const canvasWidth = layoutCanvasEl.clientWidth;
  const canvasHeight = Math.max(
    layoutCanvasEl.clientHeight,
    globalThis.innerHeight || 0,
  );
  const renderableItems = getRenderableItems(snapshot);
  const textItems = [];
  const fragment = document.createDocumentFragment();

  // Text items are rebuilt each render; the cover art element is persistent
  // (managed by updateCoverArt) so it is not torn down and re-fetched here.
  Array.from(layoutCanvasEl.querySelectorAll(".layout-item")).forEach((node) => {
    node.remove();
  });

  let coverArtItem = null;
  renderableItems.forEach((item) => {
    const fieldName = String(item.field || "").trim();
    const text = String(item.text || "").trim();
    if (fieldName === "%CoverArt") {
      coverArtItem = item;
      return;
    }

    if (!text) {
      return;
    }

    textItems.push(item);
  });

  updateCoverArt(coverArtItem, snapshot, canvasWidth, canvasHeight);

  textItems.sort((leftItem, rightItem) => {
    const verticalDelta =
      Number(leftItem?.position?.[0] ?? 0) -
      Number(rightItem?.position?.[0] ?? 0);
    if (verticalDelta !== 0) {
      return verticalDelta;
    }

    const horizontalDelta =
      Number(leftItem?.position?.[1] ?? 0) -
      Number(rightItem?.position?.[1] ?? 0);
    if (horizontalDelta !== 0) {
      return horizontalDelta;
    }

    return Number(leftItem?.index ?? 0) - Number(rightItem?.index ?? 0);
  });

  let layouts = textItems.map((item) =>
    layoutTextItem(item, String(item.text || "").trim(), canvasWidth, canvasHeight),
  );
  layouts = fitLayoutsVertically(layouts, canvasWidth, canvasHeight);

  const rowOffsets = computeRowOffsets(layouts);
  layouts.forEach((layout, index) => {
    fragment.append(buildTextItemElement(layout, canvasWidth, rowOffsets[index]));
  });

  layoutCanvasEl.append(fragment);
  // The "Waiting for Beam" placeholder is setup guidance only: keep it hidden
  // whenever a mood layout exists, even if every item is inactive, hidden or
  // empty (e.g. a cortina at the end of the playlist with no next tanda) —
  // the native display shows just the background in that case.
  emptyStateEl.hidden =
    getDisplayItems(snapshot).length > 0 ||
    layoutCanvasEl.querySelectorAll(".layout-item, .layout-cover-art").length >
      0;
}

function buildBackgroundRenderKey(snapshot) {
  const background = snapshot?.background || {};
  const baseLayer = background.base || {};
  const overlayLayer = background.overlay || {};

  return JSON.stringify({
    genre: normalizeGenre(snapshot?.currentSong),
    base: {
      available: Boolean(baseLayer.available),
      kind: String(baseLayer.kind || ""),
      mode: String(baseLayer.mode || ""),
      opacity: Number(baseLayer.opacity ?? 100),
      improveReadability: Boolean(baseLayer.improveReadability),
      readability: Number(baseLayer.readability ?? 0),
      currentPath: String(baseLayer.currentPath || ""),
      sourcePath: String(baseLayer.sourcePath || ""),
      canonicalReference: String(baseLayer.canonicalReference || ""),
    },
    overlay: {
      available: Boolean(overlayLayer.available),
      kind: String(overlayLayer.kind || ""),
      mode: String(overlayLayer.mode || ""),
      opacity: Number(overlayLayer.opacity ?? 100),
      currentPath: String(overlayLayer.currentPath || ""),
      sourcePath: String(overlayLayer.sourcePath || ""),
      canonicalReference: String(overlayLayer.canonicalReference || ""),
    },
  });
}

function parseBackgroundLayerColor(layer) {
  const reference = String(
    layer?.canonicalReference || layer?.currentPath || layer?.sourcePath || "",
  ).trim();
  const match = reference.match(/^color:#?([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/);
  return match ? `#${match[1]}` : "";
}

// Load a decoded image off-screen, then swap a CSS variable to its blob object
// URL. The current background stays up until the new one is fully decoded, so the
// switch is direct (no fade) and flash-free. The renderKey guard drops stale
// loads so a newer background that arrived meanwhile is never overwritten.
async function setBackgroundImageFromUrl(cssVar, url, renderKey) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`background request failed: ${response.status}`);
    }
    const objectUrl = URL.createObjectURL(await response.blob());
    const decoder = new Image();
    decoder.src = objectUrl;
    if (typeof decoder.decode === "function") {
      await decoder.decode().catch(() => {});
    }
    if (renderKey !== lastBackgroundRenderKey) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    document.body.style.setProperty(cssVar, `url("${objectUrl}")`);
    const previousObjectUrl = backgroundObjectUrls[cssVar];
    backgroundObjectUrls[cssVar] = objectUrl;
    if (previousObjectUrl) {
      URL.revokeObjectURL(previousObjectUrl);
    }
  } catch {
    // Leave the current background in place on failure rather than blanking it.
  }
}

function clearBackgroundImage(cssVar) {
  document.body.style.removeProperty(cssVar);
  const previousObjectUrl = backgroundObjectUrls[cssVar];
  if (previousObjectUrl) {
    URL.revokeObjectURL(previousObjectUrl);
    backgroundObjectUrls[cssVar] = "";
  }
}

function buildBackgroundLayerUrl(layerName, layer) {
  const params = new URLSearchParams();
  const resolvedPath = String(layer?.currentPath || layer?.sourcePath || "");
  const layerKind = String(layer?.kind || "");

  if (resolvedPath) {
    params.set("path", resolvedPath);
  }
  if (layerKind) {
    params.set("kind", layerKind);
  }

  return `/media/background/${layerName}?${params.toString()}`;
}

function applyBackground(snapshot) {
  const background = snapshot.background || {};
  const baseLayer = background.base || {};
  const overlayLayer = background.overlay || {};
  const nextBackgroundRenderKey = buildBackgroundRenderKey(snapshot);
  const overlayMode = String(overlayLayer.mode || "")
    .trim()
    .toLowerCase();

  const showBase = Boolean(baseLayer.available) && overlayMode !== "replace";
  const showOverlay = Boolean(overlayLayer.available) && overlayMode !== "off";
  const overlayOpacity =
    overlayMode === "blend"
      ? Math.max(0, Math.min(1, Number(overlayLayer.opacity ?? 100) / 100))
      : 1;
  // Match the native display: blend uses the configured opacity directly
  // (100 -> fully opaque, hiding the base), replace is always opaque.
  const overlayRenderOpacity =
    overlayMode === "replace" ? 1 : overlayOpacity;

  if (nextBackgroundRenderKey === lastBackgroundRenderKey) {
    return;
  }

  lastBackgroundRenderKey = nextBackgroundRenderKey;

  // "Improve readability": keep the existing background but blur + dim it.
  const baseImproveReadability = Boolean(baseLayer.improveReadability) && showBase;
  const baseReadability = Math.max(0, Math.min(100, Number(baseLayer.readability ?? 0)));
  const readabilityActive = baseImproveReadability && baseReadability > 0;

  document.body.classList.toggle("with-background-base", showBase);
  document.body.classList.toggle("with-background-overlay", showOverlay);
  document.body.classList.toggle("readability-active", readabilityActive);

  if (readabilityActive) {
    document.body.style.setProperty(
      "--beam-readability-blur",
      `${baseReadability * 0.2}px`,
    );
    document.body.style.setProperty(
      "--beam-readability-dim",
      String(baseReadability * 0.005),
    );
  } else {
    document.body.style.removeProperty("--beam-readability-blur");
    document.body.style.removeProperty("--beam-readability-dim");
  }

  const baseIsColor =
    String(baseLayer.kind || "").trim().toLowerCase() === "color";
  const baseColor = baseIsColor ? parseBackgroundLayerColor(baseLayer) : "";

  if (showBase && baseColor) {
    // Solid color background: fill with the color, no image (matches native).
    document.body.style.setProperty("--beam-background-base-color", baseColor);
    clearBackgroundImage("--beam-background-base");
  } else if (showBase && baseLayer.url) {
    setBackgroundImageFromUrl(
      "--beam-background-base",
      buildBackgroundLayerUrl("base", baseLayer),
      nextBackgroundRenderKey,
    );
    document.body.style.removeProperty("--beam-background-base-color");
  } else {
    clearBackgroundImage("--beam-background-base");
    document.body.style.removeProperty("--beam-background-base-color");
  }

  const overlayIsColor =
    String(overlayLayer.kind || "").trim().toLowerCase() === "color";
  const overlayColor = overlayIsColor ? parseBackgroundLayerColor(overlayLayer) : "";

  if (showOverlay && overlayColor) {
    document.body.style.setProperty("--beam-background-overlay-color", overlayColor);
    clearBackgroundImage("--beam-background-overlay");
    document.body.style.setProperty(
      "--beam-background-overlay-opacity",
      String(overlayRenderOpacity),
    );
  } else if (showOverlay && overlayLayer.url) {
    setBackgroundImageFromUrl(
      "--beam-background-overlay",
      buildBackgroundLayerUrl("overlay", overlayLayer),
      nextBackgroundRenderKey,
    );
    document.body.style.removeProperty("--beam-background-overlay-color");
    document.body.style.setProperty(
      "--beam-background-overlay-opacity",
      String(overlayRenderOpacity),
    );
  } else {
    clearBackgroundImage("--beam-background-overlay");
    document.body.style.removeProperty("--beam-background-overlay-color");
    document.body.style.removeProperty("--beam-background-overlay-opacity");
  }

  document.body.classList.remove("genre-tango", "genre-vals", "genre-milonga");
  const genre = normalizeGenre(snapshot.currentSong);
  const themeGenre = hasEnabledMoodTheme(snapshot, genre) ? genre : "";
  if (themeGenre) {
    document.body.classList.add(`genre-${themeGenre}`);
  }
}

function applyDisplayOverrides(snapshot) {
  // Final overrides drawn on top of the normal display: blackout replaces the
  // output with a black screen, and the temporary message renders above it.
  const blackoutActive = Boolean(snapshot?.blackout);
  if (blackoutLayerEl) {
    blackoutLayerEl.hidden = !blackoutActive;
  }

  const tempMessage = snapshot?.tempMessage || {};
  const messageActive = Boolean(tempMessage.active) && String(tempMessage.text || "").trim();
  if (tempMessageOverlayEl && tempMessagePanelEl) {
    if (messageActive) {
      tempMessagePanelEl.innerHTML = escapeHtml(String(tempMessage.text)).replaceAll(
        "\n",
        "<br>",
      );
      tempMessageOverlayEl.classList.toggle("over-blackout", blackoutActive);
      tempMessageOverlayEl.hidden = false;
    } else {
      tempMessageOverlayEl.hidden = true;
      tempMessagePanelEl.textContent = "";
    }
  }
}

function renderSnapshot(snapshot, sequence) {
  lastSnapshot = snapshot;
  lastSequence = sequence || 0;
  document.title = snapshot?.currentSong?.title
    ? `Beam Remote Display - ${snapshot.currentSong.title}`
    : "Beam Remote Display";
  renderLayout(snapshot);
  applyBackground(snapshot);
  applyDisplayOverrides(snapshot);
}

function rerenderCurrentSnapshot() {
  if (!lastSnapshot) {
    return;
  }
  renderLayout(lastSnapshot);
}

async function loadInitialState() {
  const response = await fetch("/now-playing", { cache: "no-store" });
  const documentState = await response.json();
  renderSnapshot(documentState.snapshot, documentState.sequence);
}

function connectEvents() {
  if (
    activeSocket?.readyState === WebSocket.OPEN ||
    activeSocket?.readyState === WebSocket.CONNECTING
  ) {
    return;
  }

  clearReconnectTimer();
  const scheme = globalThis.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(
    `${scheme}://${globalThis.location.host}/events`,
  );
  activeSocket = socket;

  socket.addEventListener("open", () => {
    reconnectDelayMs = 1000;
    void requestWakeLock();
  });

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    renderSnapshot(payload.snapshot, payload.sequence);
  });

  socket.addEventListener("close", () => {
    if (activeSocket === socket) {
      activeSocket = null;
    }
    scheduleReconnect();
  });

  socket.addEventListener("error", () => {
    socket.close();
  });
}

installDisplayActivationHandlers();
globalThis.addEventListener("resize", rerenderCurrentSnapshot);
document.addEventListener("fullscreenchange", rerenderCurrentSnapshot);

try {
  await loadInitialState();
} finally {
  connectEvents();
}
