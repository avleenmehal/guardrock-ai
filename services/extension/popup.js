// popup.js

const toggle = document.getElementById('toggle');
const status = document.getElementById('status');

chrome.storage.local.get('enabled', (result) => {
  const enabled = result.enabled !== false;
  toggle.checked = enabled;
  status.textContent = enabled ? 'ON' : 'OFF';
});

toggle.addEventListener('change', () => {
  const enabled = toggle.checked;
  chrome.storage.local.set({ enabled });
  status.textContent = enabled ? 'ON' : 'OFF';
});