// Background service worker

// Create context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'saveMcpMemory',
    title: 'Save to MCP Memory',
    contexts: ['selection'],
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'saveMcpMemory' && info.selectionText) {
    saveToMemory(info.selectionText, tab);
  }
});

async function saveToMemory(text, tab) {
  try {
    const memory = {
      content: text,
      type: 'note',
      source: 'browser',
      project: 'web-browsing',
      context: {
        url: tab.url,
        title: tab.title,
      },
      importance: 'medium',
    };

    await fetch('http://localhost:8000/memories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memory),
    });

    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'MCP Memory',
      message: 'Selection saved successfully!',
    });
  } catch (error) {
    console.error('Failed to save:', error);
  }
}
