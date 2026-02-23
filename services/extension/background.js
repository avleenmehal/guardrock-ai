// background.js

const BACKEND_URL = 'http://152.7.179.48:3000/api/submit';
const PULL_URL = 'http://152.7.179.25:3001/api/consume/';
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

async function publishToBackend(payload, attempt = 1) {
  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error(`Server responded with ${response.status}`);

    const data = await response.json();
    console.log('[Background] Published successfully:', data);
    return { success: true, data };
  } catch (error) {
    console.warn(`[Background] Attempt ${attempt}/${MAX_RETRIES} failed:`, error.message);

    if (attempt < MAX_RETRIES) {
      const delay = RETRY_DELAY_MS * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return publishToBackend(payload, attempt + 1);
    }

    console.error('[Background] All retries exhausted. Dropping message.');
    return { success: false, error: error.message };
  }
}

async function pullFromBackend() {
  try {
    const response = await fetch(PULL_URL);
    if (!response.ok) throw new Error(`Status ${response.status}`);

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.warn('[Background] Pull failed:', error.message);
    return { success: false, error: error.message };
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'VIDEO_WATCHED') {
    console.log('[Background] Received video metadata:', message.payload);
    publishToBackend(message.payload);
    return;
  }

  if (message.type === 'POLL_REQUEST') {
    pullFromBackend().then((result) => {
      sendResponse(result);
    });
    return true; // keep channel open for async response
  }
});