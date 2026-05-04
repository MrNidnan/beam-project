const layoutCanvasEl = document.getElementById("layout-canvas");
const emptyStateEl = document.getElementById("empty-state");
const textMeasurerEl = document.getElementById("text-measurer");

const COVER_ART_URL = "/media/cover-art/current";
const ABSOLUTE_MIN_TEXT_SIZE_PX = 10;
const ABSOLUTE_MAX_TEXT_SIZE_PX = 420;
const FULLSCREEN_MULTIPLIER_START_PX = 1440;
const FULLSCREEN_MULTIPLIER_RANGE_PX = 1440;
const FULLSCREEN_MULTIPLIER_MAX = 1.35;

let screenWakeLock = null;
let wakeLockBound = false;
let reconnectDelayMs = 1000;
let reconnectTimer = null;
let activeSocket = null;
let lastSnapshot = null;
let lastSequence = 0;

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

function getFullscreenTextMultiplier() {
  if (!document.fullscreenElement) {
    return 1;
  }

  const screenLongestEdge = Math.max(screen.width || 0, screen.height || 0);
  if (screenLongestEdge <= FULLSCREEN_MULTIPLIER_START_PX) {
    return 1;
  }

  const normalizedBoost = Math.min(
    1,
    (screenLongestEdge - FULLSCREEN_MULTIPLIER_START_PX) /
      FULLSCREEN_MULTIPLIER_RANGE_PX,
  );

  return 1 + normalizedBoost * (FULLSCREEN_MULTIPLIER_MAX - 1);
}

function getItemFontSizePx(item, canvasHeight) {
  const baseFontSizePx = getBaseItemFontSizePx(item, canvasHeight);
  const boostedFontSizePx = Math.round(
    baseFontSizePx * getFullscreenTextMultiplier(),
  );

  return Math.min(
    ABSOLUTE_MAX_TEXT_SIZE_PX,
    Math.max(baseFontSizePx, boostedFontSizePx),
  );
}

function getFontFamily(item) {
  const fontFace = String(item.font || "").trim();
  if (!fontFace) {
    return '"Palatino Linotype", "Book Antiqua", Palatino, "Liberation Sans", serif';
  }

  return `${fontFace}, "Liberation Sans", serif`;
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
  textMeasurerEl.style.fontSize = `${Math.max(ABSOLUTE_MIN_TEXT_SIZE_PX, fontSizePx)}px`;
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
    let splitIndex = 1;
    while (splitIndex <= remaining.length) {
      const candidate = remaining.slice(0, splitIndex);
      const candidateWidth = measureSingleLineText(
        candidate,
        item,
        fontSizePx,
      ).width;
      if (candidateWidth > maxWidthPx) {
        splitIndex = Math.max(1, splitIndex - 1);
        break;
      }
      splitIndex += 1;
    }

    if (splitIndex > remaining.length) {
      splitIndex = remaining.length;
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
  const positionX = Number(item?.position?.[1] ?? 0);
  if (alignment === "center") {
    return canvasWidth;
  }
  return Math.max(0, ((100 - positionX) / 100) * canvasWidth);
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

function createCoverArtElement(
  item,
  snapshot,
  sequence,
  canvasWidth,
  canvasHeight,
) {
  const coverArt = snapshot.coverArt || {};
  const isAvailable = Boolean(coverArt.available ?? snapshot.coverArtAvailable);
  if (!isAvailable) {
    return null;
  }

  const coverArtEl = document.createElement("img");
  const alignment = normalizeAlignment(item.alignment);
  const sizePx = Math.max(
    48,
    Math.round((Number(item.size || 0) / 100) * canvasHeight),
  );
  const topPx = Math.round(
    (Number(item?.position?.[0] ?? 0) / 100) * canvasHeight,
  );

  coverArtEl.className = `layout-cover-art align-${alignment}`;
  coverArtEl.alt = snapshot.currentSong?.title
    ? `${snapshot.currentSong.title} cover art`
    : "Current cover art";
  coverArtEl.src = `${coverArt.url || COVER_ART_URL}?v=${sequence}`;
  coverArtEl.width = sizePx;
  coverArtEl.height = sizePx;
  coverArtEl.style.top = `${topPx}px`;
  coverArtEl.style.width = `${sizePx}px`;
  coverArtEl.style.height = `${sizePx}px`;

  applyHorizontalPosition(coverArtEl, alignment, item, canvasWidth);
  return coverArtEl;
}

function createTextItemElement(
  item,
  text,
  canvasWidth,
  canvasHeight,
  extraVerticalOffset,
) {
  const alignment = normalizeAlignment(item.alignment);
  const textFlow = normalizeTextFlow(item.textFlow);
  const itemEl = document.createElement("p");
  const baseFontSizePx = getBaseItemFontSizePx(item, canvasHeight);
  let fontSizePx = getItemFontSizePx(item, canvasHeight);
  const { lineHeightPx, lineSpacingPx } = getMeasuredLineSpacing(
    item,
    fontSizePx,
  );
  const maxWidthPx = getItemMaxWidth(canvasWidth, item, alignment);
  let renderedText = text;
  let extraHeightPx = 0;

  if (textFlow === "scale") {
    let measurement = measureSingleLineText(text, item, fontSizePx);
    while (
      fontSizePx > baseFontSizePx &&
      measurement.width > maxWidthPx * 0.95
    ) {
      fontSizePx = Math.max(baseFontSizePx, Math.floor(fontSizePx * 0.9));
      measurement = measureSingleLineText(text, item, fontSizePx);
    }
  }

  if (textFlow === "cut") {
    renderedText = trimCutText(text, item, maxWidthPx, fontSizePx);
  }

  if (textFlow === "wrap") {
    const wrappedLines = wrapTextLines(text, item, fontSizePx, maxWidthPx);
    renderedText = wrappedLines.join("\n");
    extraHeightPx = Math.max(0, (wrappedLines.length - 1) * lineSpacingPx);
  }

  itemEl.className = `layout-item align-${alignment} flow-${textFlow}`;
  itemEl.dataset.field = String(item.field || "").replaceAll("%", "") || "text";
  itemEl.innerHTML = escapeHtml(renderedText).replaceAll("\n", "<br>");
  itemEl.style.top = `${Math.round((Number(item?.position?.[0] ?? 0) / 100) * canvasHeight) + extraVerticalOffset}px`;
  itemEl.style.color = parseFontColor(item.fontColor);
  itemEl.style.fontFamily = getFontFamily(item);
  itemEl.style.fontSize = `${fontSizePx}px`;
  itemEl.style.fontStyle = normalizeStyle(item.style);
  itemEl.style.fontWeight = normalizeWeight(item.weight);
  itemEl.style.width = `${Math.max(0, maxWidthPx)}px`;
  itemEl.style.lineHeight =
    textFlow === "wrap" ? `${lineSpacingPx}px` : `${lineHeightPx}px`;

  applyHorizontalPosition(itemEl, alignment, item, canvasWidth);

  return { element: itemEl, extraHeightPx };
}

function getRenderableItems(snapshot) {
  const configuredItems = getDisplayItems(snapshot).filter((item) =>
    isItemActive(item),
  );
  if (configuredItems.length > 0) {
    return configuredItems;
  }
  return buildFallbackDisplayItems(snapshot);
}

function renderLayout(snapshot, sequence) {
  const canvasWidth = layoutCanvasEl.clientWidth;
  const canvasHeight = layoutCanvasEl.clientHeight;
  const renderableItems = getRenderableItems(snapshot);
  const textItems = [];
  const fragment = document.createDocumentFragment();

  Array.from(
    layoutCanvasEl.querySelectorAll(".layout-item, .layout-cover-art"),
  ).forEach((node) => {
    node.remove();
  });

  renderableItems.forEach((item) => {
    const fieldName = String(item.field || "").trim();
    const text = String(item.text || "").trim();
    if (fieldName === "%CoverArt") {
      const coverArtEl = createCoverArtElement(
        item,
        snapshot,
        sequence,
        canvasWidth,
        canvasHeight,
      );
      if (coverArtEl) {
        fragment.append(coverArtEl);
      }
      return;
    }

    if (!text) {
      return;
    }

    textItems.push(item);
  });

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

  let cumulativeVerticalOffset = 0;
  let currentRowPosition = null;
  let currentRowExtraHeight = 0;

  textItems.forEach((item) => {
    const rowPosition = Number(item?.position?.[0] ?? 0);
    if (currentRowPosition === null) {
      currentRowPosition = rowPosition;
    } else if (rowPosition > currentRowPosition) {
      cumulativeVerticalOffset += currentRowExtraHeight;
      currentRowExtraHeight = 0;
      currentRowPosition = rowPosition;
    }

    const text = String(item.text || "").trim();
    const renderedTextItem = createTextItemElement(
      item,
      text,
      canvasWidth,
      canvasHeight,
      cumulativeVerticalOffset,
    );
    fragment.append(renderedTextItem.element);
    currentRowExtraHeight = Math.max(
      currentRowExtraHeight,
      renderedTextItem.extraHeightPx,
    );
  });

  layoutCanvasEl.append(fragment);
  emptyStateEl.hidden =
    layoutCanvasEl.querySelectorAll(".layout-item, .layout-cover-art").length >
    0;
}

function applyBackground(snapshot, sequence) {
  const background = snapshot.background || {};
  const baseLayer = background.base || {};
  const overlayLayer = background.overlay || {};
  const overlayMode = String(overlayLayer.mode || "")
    .trim()
    .toLowerCase();

  const showBase = Boolean(baseLayer.available) && overlayMode !== "replace";
  const showOverlay = Boolean(overlayLayer.available) && overlayMode !== "off";
  const overlayOpacity =
    overlayMode === "blend"
      ? Math.max(0, Math.min(1, Number(overlayLayer.opacity ?? 100) / 100))
      : 1;
  const overlayRenderOpacity =
    overlayMode === "replace" ? 1 : 0.18 * overlayOpacity;

  document.body.classList.toggle("with-background-base", showBase);
  document.body.classList.toggle("with-background-overlay", showOverlay);

  if (showBase && baseLayer.url) {
    document.body.style.setProperty(
      "--beam-background-base",
      `url("${baseLayer.url}?v=${sequence}")`,
    );
  } else {
    document.body.style.removeProperty("--beam-background-base");
  }

  if (showOverlay && overlayLayer.url) {
    document.body.style.setProperty(
      "--beam-background-overlay",
      `url("${overlayLayer.url}?v=${sequence}")`,
    );
    document.body.style.setProperty(
      "--beam-background-overlay-opacity",
      String(overlayRenderOpacity),
    );
  } else {
    document.body.style.removeProperty("--beam-background-overlay");
    document.body.style.removeProperty("--beam-background-overlay-opacity");
  }

  document.body.classList.remove("genre-tango", "genre-vals", "genre-milonga");
  const genre = normalizeGenre(snapshot.currentSong);
  if (genre) {
    document.body.classList.add(`genre-${genre}`);
  }
}

function renderSnapshot(snapshot, sequence) {
  lastSnapshot = snapshot;
  lastSequence = sequence || 0;
  document.title = snapshot?.currentSong?.title
    ? `Beam Remote Display - ${snapshot.currentSong.title}`
    : "Beam Remote Display";
  renderLayout(snapshot, sequence || 0);
  applyBackground(snapshot, sequence || 0);
}

function rerenderCurrentSnapshot() {
  if (!lastSnapshot) {
    return;
  }
  renderLayout(lastSnapshot, lastSequence);
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
