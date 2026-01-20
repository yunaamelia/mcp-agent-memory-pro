// Content script for browser extension

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSelection') {
    const selectedText = window.getSelection().toString();
    sendResponse({ text: selectedText });
  }
});

// Add context menu for quick save
document.addEventListener('mouseup', () => {
  const selectedText = window.getSelection().toString();
  if (selectedText.length > 0) {
    // Could show a floating button to quick-save
  }
});
