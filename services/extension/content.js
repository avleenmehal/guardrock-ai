(function () {

  // ---- CONSTANTS ----
  const WATCH_THRESHOLD_MS = 3000;
  const PULL_URL = 'http://152.7.177.184:3001/api/consume/';
  const POLL_INTERVAL_MS = 1000;

  const processedVideos = new Set();
  let currentTimer = null;
  let currentVideoId = null;
  let pollInterval = null;

  // ---- VIDEO ID EXTRACTION ----
  function getVideoId() {
    const match = window.location.pathname.match(/\/shorts\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }

  // ---- ACTIVE RENDERER ----
  function getActiveRenderer() {
    const renderers = document.querySelectorAll('ytd-reel-video-renderer');
    for (const el of renderers) {
      const rect = el.getBoundingClientRect();
      if (rect.top >= 0 && rect.top < window.innerHeight) {
        return el;
      }
    }
    return null;
  }

  // ---- METADATA EXTRACTION ----
  function extractMetadata(videoId) {
    const renderer = getActiveRenderer();
    const scope = renderer || document;

    const title =
      scope.querySelector(
        'yt-shorts-video-title-view-model .yt-core-attributed-string'
      )?.textContent?.trim() ||
      scope.querySelector('#title')?.textContent?.trim() ||
      '';

    const channel =
      scope.querySelector('a[href^="/@"]')?.textContent?.trim()?.replace(/^@/, '') ||
      '';

    const description =
      scope.querySelector(
        'yt-shorts-video-title-view-model + yt-attributed-string'
      )?.textContent?.trim() ||
      '';

    return {
      unique_id: videoId,
      url: window.location.href,
      title: title,
      channel_name: channel,
      description: description,
      timestamp: Date.now(),
    };
  }

  // ---- TRACKING ----
  function startTracking(videoId) {
    if (processedVideos.has(videoId)) return;

    clearTimeout(currentTimer);
    currentVideoId = videoId;

    currentTimer = setTimeout(() => {
      if (getVideoId() !== videoId) return;
      if (processedVideos.has(videoId)) return;

      processedVideos.add(videoId);
      const metadata = extractMetadata(videoId);

      chrome.runtime.sendMessage({ type: 'VIDEO_WATCHED', payload: metadata });
      console.log('[VideoTracker] Processed:', videoId);
    }, WATCH_THRESHOLD_MS);
  }

  function stopTracking() {
    clearTimeout(currentTimer);
    currentTimer = null;
    currentVideoId = null;
  }

  function isEnabled(callback) {
    chrome.storage.local.get('enabled', (result) => {
      callback(result.enabled !== false);
    });
  }

  function handleNavigation() {
    isEnabled((enabled) => {
      if (!enabled) {
        stopTracking();
        return;
      }

      const videoId = getVideoId();
      if (!videoId) {
        stopTracking();
        return;
      }

      startTracking(videoId);
    });
  }

  // ---- SPA OBSERVER ----
  const observer = new MutationObserver(() => {
    const videoId = getVideoId();
    if (videoId && videoId !== currentVideoId) {
      handleNavigation();
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener('popstate', handleNavigation);
  handleNavigation();

  // ---- TOGGLE LISTENER ----
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.enabled) {
      if (changes.enabled.newValue === false) {
        stopTracking();
        stopPolling();
      } else {
        handleNavigation();
        startPolling();
      }
    }
  });

  // ============================================================
  //  OVERLAY UI + POLLING (pull from backend)
  // ============================================================

  // ---- CREATE OVERLAY ----
  function createOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'video-tracker-overlay';
    overlay.innerHTML = `
      <style>
        #video-tracker-overlay {
          position: fixed;
          top: 16px;
          right: 16px;
          width: 280px;
          max-height: 400px;
          overflow-y: auto;
          background: rgba(15, 15, 15, 0.92);
          color: #eee;
          border-radius: 12px;
          padding: 14px;
          font-family: -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 13px;
          z-index: 99999;
          box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        #video-tracker-overlay .vt-header {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 10px;
          color: #fff;
        }
        #video-tracker-overlay .vt-card {
          background: rgba(255,255,255,0.08);
          border-radius: 8px;
          padding: 10px;
          margin-bottom: 8px;
        }
        #video-tracker-overlay .vt-title {
          font-weight: 600;
          color: #fff;
          margin-bottom: 3px;
        }
        #video-tracker-overlay .vt-channel {
          font-size: 11px;
          color: #999;
          margin-bottom: 6px;
        }
        #video-tracker-overlay .vt-summary {
          font-size: 12px;
          line-height: 1.4;
          color: #ccc;
        }
        #video-tracker-overlay .vt-empty {
          color: #666;
          text-align: center;
          padding: 12px 0;
        }
        #video-tracker-overlay .vt-level {
          display: inline-block;
          font-size: 11px;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 4px;
          margin-bottom: 6px;
        }
        #video-tracker-overlay .vt-level.safe {
          display: none;
        }
        #video-tracker-overlay .vt-level.warning {
          background: rgba(255, 200, 0, 0.2);
          color: #ffc800;
        }
        #video-tracker-overlay .vt-level.danger {
          background: rgba(255, 50, 50, 0.2);
          color: #ff4444;
        }
      </style>
      <div class="vt-header">Video Insights</div>
      <div id="vt-feed">
        <div class="vt-empty">Waiting for data...</div>
      </div>
    `;
    document.body.appendChild(overlay);
    return document.getElementById('vt-feed');
  }

  // ---- ESCAPE HTML ----
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- LEVEL INFO ----
  function getLevelInfo(level) {
    const n = Number(level);
    if (n >= 8) return { className: 'danger', label: `⚠ High Risk (${n}/10)` };
    if (n >= 4) return { className: 'warning', label: `⚠ Caution (${n}/10)` };
    return { className: 'safe', label: '' };
  }

  // ---- RENDER FEED ----
  function renderFeed(feedEl, items) {
    feedEl.innerHTML = '';
    items.forEach((item) => {
      const level = getLevelInfo(item.level);
      const card = document.createElement('div');
      card.className = 'vt-card';
      card.innerHTML = `
        <div class="vt-level ${level.className}">${level.label}</div>
        <div class="vt-title">${escapeHtml(item.title || 'Untitled')}</div>
        <div class="vt-channel">${escapeHtml(item.channel_name || 'Unknown channel')}</div>
        <div class="vt-summary">${escapeHtml(item.summary || 'No summary available')}</div>
      `;
      feedEl.appendChild(card);
    });
  }

  // ---- POLLING ----
  const feedEl = createOverlay();

  async function poll() {
    try {
      const response = await fetch(PULL_URL);
      if (!response.ok) throw new Error(`Status ${response.status}`);

      const data = await response.json();
      const items = Array.isArray(data) ? data : [data];

      if (items.length === 0) return;
      renderFeed(feedEl, items);
    } catch (error) {
      console.warn('[VideoTracker] Poll failed:', error.message);
    }
  }

  function startPolling() {
    if (pollInterval) return;
    poll();
    pollInterval = setInterval(poll, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    clearInterval(pollInterval);
    pollInterval = null;
  }

  // ---- Start polling based on initial toggle state ----
  isEnabled((enabled) => {
    if (enabled) startPolling();
  });

})();