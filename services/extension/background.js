//Constants for the backend URL, maximum retries, and retry delay
const BACKEND_URL = 'http://152.7.179.59:3000/api/submit/';
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

//Mock function
async function publishToBackendMock(payload) {
  console.log('[Background] MOCK PUBLISH — would send to backend:', payload);
  return { success: true, data: payload };
}


// Function to publish the metadata to the backend. It retries for up to 3 times with a delay of 1 second between retries.
async function publishToBackend(payload, attempt = 1) {
  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();
    console.log('[Background] Published successfully:', data);
    return { success: true, data };
  } catch (error) {
    console.warn(
      `[Background] Attempt ${attempt}/${MAX_RETRIES} failed:`,
      error.message
    );

    if (attempt < MAX_RETRIES) {
      const delay = RETRY_DELAY_MS * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return publishToBackend(payload, attempt + 1);
    }

    console.error('[Background] All retries exhausted. Dropping message.');
    return { success: false, error: error.message };
  }
}

//Message listener: receives from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== 'VIDEO_WATCHED') return;

  console.log('[Background] Received video metadata:', message.payload);

  publishToBackend(message.payload).then((result) => {
    sendResponse(result);
  });

  return true;
});