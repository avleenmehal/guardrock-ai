//Immediately-invoked function expression (IIFE)
(function () {

  //Constants for the video tracker
  const WATCH_THRESHOLD_MS = 3000;

  //Set to store the already processed videos
  const processedVideos = new Set();

  //Variables to store the current timer and video ID
  let currentTimer = null;
  let currentVideoId = null;

  //Extract video ID from URL
  function getVideoId() {
    //Regex pattern matching on video URL
    const match = window.location.pathname.match(/\/shorts\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }

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

  //Extract metadata from the video
  function extractMetadata(videoId) {
    const renderer = getActiveRenderer();
    // Fall back to document if renderer not found
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
      video_unique_id: videoId,
      video_url: window.location.href,
      video_title: title,
      channel_name: channel,
      video_description: description,
      timestamp: Date.now(),
    };
  }

  // Function to start tracking a video
  function startTracking(videoId) {
    // If the video has already been processed in this session, skip
    if (processedVideos.has(videoId)) return;

    // Clear any existing timer (user swiped before 3 seconds)
    clearTimeout(currentTimer);
    currentVideoId = videoId;

    currentTimer = setTimeout(() => {
      //If the user is on the same video after 3 seconds, process the video
      if (getVideoId() !== videoId) return;
      if (processedVideos.has(videoId)) return;

      processedVideos.add(videoId);
      const metadata = extractMetadata(videoId);

      // Send the metadata to the background service worker
      chrome.runtime.sendMessage(
        { type: 'VIDEO_WATCHED', payload: metadata },
        (response) => {
          if (chrome.runtime.lastError) {
            console.error('[VideoTracker] Message failed:', chrome.runtime.lastError.message);
          }
        }
      );

      console.log('[VideoTracker] Processed:', videoId);
    }, WATCH_THRESHOLD_MS);
  }

  // Function to stop tracking a video
  function stopTracking() {
    clearTimeout(currentTimer);
    currentTimer = null;
    currentVideoId = null;
  }

  // Function to check if the extension is enabled
  function isEnabled(callback) {
    chrome.storage.local.get('enabled', (result) => {
      // Default to enabled if not set
      callback(result.enabled !== false);
    });
  }

  // Function to handle navigation
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

  // Function to watch for SPA route changes - MutationObserver because of the single page application nature of YouTube Shorts which doesn't reload the page when the user navigates to a new video
  const observer = new MutationObserver(() => {
    const videoId = getVideoId();
    // Only react if the video actually changed
    if (videoId && videoId !== currentVideoId) {
      handleNavigation();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  //Also listen for popstate (back/forward navigation)
  window.addEventListener('popstate', handleNavigation);

  // Initial check on injection
  handleNavigation();

  // Listen for toggle changes in real-time
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.enabled) {
      if (changes.enabled.newValue === false) {
        stopTracking();
      } else {
        handleNavigation();
      }
    }
  });
})();