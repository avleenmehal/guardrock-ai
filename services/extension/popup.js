const toggle = document.getElementById('toggle');
const status = document.getElementById('status');

// Load saved state on popup open
chrome.storage.local.get('enabled', (result) => {
  const enabled = result.enabled !== false; // default to true
  toggle.checked = enabled;
  status.textContent = enabled ? 'ON' : 'OFF';
});

// Persist state on toggle
toggle.addEventListener('change', () => {
  const enabled = toggle.checked;
  chrome.storage.local.set({ enabled });
  status.textContent = enabled ? 'ON' : 'OFF';
});