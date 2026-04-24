const titleEl = document.getElementById("title");
const artistNameEl = document.getElementById("artist-name");
const previousSongEl = document.getElementById("previous-song");
const currentDateEl = document.getElementById("current-date");

let screenWakeLock = null;
let wakeLockBound = false;
let reconnectDelayMs = 1000;
let reconnectTimer = null;
let activeSocket = null;

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

function formatSong(song) {
  if (!song) {
    return "-";
  }

  const parts = [song.title, song.artist, song.albumArtist].filter(Boolean);
  return parts.length ? parts.join(" - ") : "Unknown track";
}

function formatArtistOrMood(song, snapshot) {
  const artist = String(song?.artist || "").trim();
  if (artist) {
    return artist;
  }

  return String(snapshot.moodName || "").trim() || "-";
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

function updateTitleScale(title) {
  const normalizedTitle = String(title || "").trim();
  let size = "default";

  if (normalizedTitle.length >= 56) {
    size = "xlong";
  } else if (normalizedTitle.length >= 42) {
    size = "long";
  } else if (normalizedTitle.length >= 30) {
    size = "medium";
  }

  titleEl.dataset.titleSize = size;
}

function applyBackground(snapshot, sequence) {
  if (snapshot.background?.available) {
    document.body.classList.add("with-background");
    document.body.style.setProperty(
      "--beam-background",
      `url("${snapshot.background.url}?v=${sequence}")`,
    );
  } else {
    document.body.classList.remove("with-background");
    document.body.style.removeProperty("--beam-background");
  }

  document.body.classList.remove("genre-tango", "genre-vals", "genre-milonga");
  const genre = normalizeGenre(snapshot.currentSong);
  if (genre) {
    document.body.classList.add(`genre-${genre}`);
  }
}

function renderSnapshot(snapshot, sequence) {
  artistNameEl.textContent = formatArtistOrMood(snapshot.currentSong, snapshot);
  const titleText = snapshot.currentSong?.title
    ? snapshot.currentSong.title
    : "Waiting for Beam";
  titleEl.textContent = titleText;
  updateTitleScale(titleText);
  const genre = normalizeGenre(snapshot.currentSong);
  currentDateEl.textContent = genre ? formatSongDate(snapshot.currentSong) : "";
  previousSongEl.textContent = formatPreviousSong(snapshot.previousSong);
  applyBackground(snapshot, sequence || 0);
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

try {
  await loadInitialState();
} finally {
  connectEvents();
}
