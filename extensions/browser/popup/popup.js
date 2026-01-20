const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', async () => {
  // Load stats
  await loadStats();

  // Search functionality
  document.getElementById('searchBtn').addEventListener('click', search);
  document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') search();
  });

  // Save page
  document.getElementById('savePageBtn').addEventListener('click', savePage);

  // Save selection
  document.getElementById('saveSelectionBtn').addEventListener('click', saveSelection);

  // Dashboard link
  document.getElementById('dashboardLink').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:8000/dashboard' });
  });
});

async function loadStats() {
  try {
    const response = await fetch(`${API_URL}/analytics/overview`);
    const data = await response.json();

    document.getElementById('totalMemories').textContent = data.total_memories || 0;

    // Get today's count (simplified)
    document.getElementById('todayCount').textContent = '0';
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

async function search() {
  const query = document.getElementById('searchInput').value;
  if (!query) return;

  try {
    const response = await fetch(`${API_URL}/memories?limit=10`);
    const data = await response.json();

    // Filter locally
    const filtered = data.memories.filter((m) =>
      m.content.toLowerCase().includes(query.toLowerCase())
    );

    displayResults(filtered);
  } catch (error) {
    console.error('Search failed:', error);
    document.getElementById('results').innerHTML = '<p>Search failed. Is the API running?</p>';
  }
}

function displayResults(memories) {
  const resultsDiv = document.getElementById('results');

  if (memories.length === 0) {
    resultsDiv.innerHTML = '<p>No results found</p>';
    return;
  }

  resultsDiv.innerHTML = memories
    .map(
      (m) => `
    <div class="result-item">
      <div class="result-title">${m.type}</div>
      <div class="result-preview">${m.content.substring(0, 100)}...</div>
    </div>
  `
    )
    .join('');
}

async function savePage() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const memory = {
      content: `${tab.title}\n\nURL: ${tab.url}`,
      type: 'note',
      source: 'browser',
      project: 'web-browsing',
      importance: 'medium',
    };

    await fetch(`${API_URL}/memories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memory),
    });

    showNotification('Page saved successfully!');
  } catch (error) {
    console.error('Failed to save page:', error);
    showNotification('Failed to save page', 'error');
  }
}

async function saveSelection() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Get selected text from content script
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'getSelection' });

    if (!response || !response.text) {
      showNotification('No text selected', 'warning');
      return;
    }

    const memory = {
      content: response.text,
      type: 'note',
      source: 'browser',
      project: 'web-browsing',
      importance: 'medium',
    };

    await fetch(`${API_URL}/memories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memory),
    });

    showNotification('Selection saved!');
  } catch (error) {
    console.error('Failed to save selection:', error);
    showNotification('Failed to save selection', 'error');
  }
}

function showNotification(message, type = 'success') {
  // Simple notification (could be enhanced)
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    padding: 12px;
    background: ${type === 'success' ? '#28a745' : '#dc3545'};
    color: white;
    border-radius: 4px;
    z-index: 1000;
  `;
  document.body.appendChild(notification);

  setTimeout(() => notification.remove(), 3000);
}
