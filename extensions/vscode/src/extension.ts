import * as vscode from 'vscode';
import axios from 'axios';

interface Memory {
  id: string;
  type: string;
  content: string;
  project?: string;
  importance_score: number;
  timestamp: number;
}

let apiUrl: string;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  console.log('MCP Memory extension activated');

  // Get configuration
  const config = vscode.workspace.getConfiguration('mcp-memory');
  apiUrl = config.get('apiUrl') || 'http://localhost:8000';

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.text = '$(database) MCP Memory';
  statusBarItem.tooltip = 'MCP Memory: Ready';
  statusBarItem.command = 'mcp-memory.dashboard';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('mcp-memory.search', searchMemories),
    vscode.commands.registerCommand('mcp-memory.store', storeSelection),
    vscode.commands.registerCommand('mcp-memory.recall', recallContext),
    vscode.commands.registerCommand('mcp-memory.suggestions', getSuggestions),
    vscode.commands.registerCommand('mcp-memory.dashboard', openDashboard)
  );

  // Register tree view providers
  const memoryProvider = new MemoryTreeProvider();
  vscode.window.registerTreeDataProvider('mcp-memory-tree', memoryProvider);

  const suggestionsProvider = new SuggestionsTreeProvider();
  vscode.window.registerTreeDataProvider('mcp-memory-suggestions', suggestionsProvider);

  // Auto-recall on file open
  if (config.get('autoRecall')) {
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        autoRecallContext(editor);
      }
    });
  }

  // Refresh suggestions periodically
  setInterval(() => {
    suggestionsProvider.refresh();
  }, 300000); // Every 5 minutes
}

async function searchMemories() {
  const query = await vscode.window.showInputBox({
    prompt: 'Search memories',
    placeHolder: 'Enter search query...',
  });

  if (!query) return;

  try {
    const response = await axios.get(`${apiUrl}/memories`, {
      params: { limit: 20 },
    });

    const memories: Memory[] = response.data.memories;

    // Filter locally for now (could use server-side search)
    const filtered = memories.filter((m) => m.content.toLowerCase().includes(query.toLowerCase()));

    if (filtered.length === 0) {
      vscode.window.showInformationMessage('No memories found');
      return;
    }

    // Show quick pick
    const items = filtered.map((m) => ({
      label: m.content.substring(0, 60) + (m.content.length > 60 ? '...' : ''),
      description: m.type,
      detail: `Project: ${m.project || 'N/A'} | Importance: ${m.importance_score.toFixed(2)}`,
      memory: m,
    }));

    const selected = await vscode.window.showQuickPick(items, {
      placeHolder: 'Select a memory to view',
    });

    if (selected) {
      showMemoryDetail(selected.memory);
    }
  } catch (error) {
    vscode.window.showErrorMessage('Failed to search memories: ' + error);
  }
}

async function storeSelection() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const selection = editor.selection;
  const content = editor.document.getText(selection);

  if (!content) {
    vscode.window.showErrorMessage('No text selected');
    return;
  }

  try {
    const project = vscode.workspace.name || 'vscode';
    const language = editor.document.languageId;
    const filePath = vscode.workspace.asRelativePath(editor.document.uri);

    // Store via API (simplified - would call MCP server in production)
    await axios.post(`${apiUrl}/memories`, {
      content,
      type: 'code',
      source: 'ide',
      project,
      language,
      file_path: filePath,
      importance: 'high',
    });

    vscode.window.showInformationMessage('Memory stored successfully!');
    statusBarItem.text = '$(check) Stored';
    setTimeout(() => {
      statusBarItem.text = '$(database) MCP Memory';
    }, 2000);
  } catch (error) {
    vscode.window.showErrorMessage('Failed to store memory: ' + error);
  }
}

async function recallContext() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  try {
    statusBarItem.text = '$(sync~spin) Recalling...';

    // Get current context
    const project = vscode.workspace.name;
    const language = editor.document.languageId;

    // Recall relevant memories (simplified API call)
    const response = await axios.get(`${apiUrl}/memories`, {
      params: {
        project,
        type: 'code',
        limit: 5,
      },
    });

    const memories: Memory[] = response.data.memories;

    if (memories.length === 0) {
      vscode.window.showInformationMessage('No relevant memories found');
      statusBarItem.text = '$(database) MCP Memory';
      return;
    }

    // Show in sidebar
    const panel = vscode.window.createWebviewPanel(
      'mcpMemoryRecall',
      'Recalled Memories',
      vscode.ViewColumn.Two,
      {}
    );

    panel.webview.html = generateRecallHtml(memories);

    statusBarItem.text = `$(lightbulb) ${memories.length} recalled`;
    setTimeout(() => {
      statusBarItem.text = '$(database) MCP Memory';
    }, 3000);
  } catch (error) {
    vscode.window.showErrorMessage('Failed to recall context: ' + error);
    statusBarItem.text = '$(database) MCP Memory';
  }
}

async function getSuggestions() {
  try {
    // Get suggestions (would call MCP suggestions tool)
    vscode.window.showInformationMessage('Getting suggestions...');

    // Placeholder for actual implementation
    const suggestions = [
      'Review: Authentication implementation',
      'TODO: Update API documentation',
      'Pattern: You typically work on tests at this time',
    ];

    const selected = await vscode.window.showQuickPick(suggestions, {
      placeHolder: 'Select a suggestion',
    });

    if (selected) {
      vscode.window.showInformationMessage(`Action: ${selected}`);
    }
  } catch (error) {
    vscode.window.showErrorMessage('Failed to get suggestions: ' + error);
  }
}

async function openDashboard() {
  const panel = vscode.window.createWebviewPanel(
    'mcpMemoryDashboard',
    'MCP Memory Dashboard',
    vscode.ViewColumn.One,
    {
      enableScripts: true,
    }
  );

  try {
    const response = await axios.get(`${apiUrl}/analytics/overview`);
    panel.webview.html = generateDashboardHtml(response.data);
  } catch (error) {
    panel.webview.html = '<h1>Error loading dashboard</h1>';
  }
}

async function autoRecallContext(editor: vscode.TextEditor) {
  // Auto-recall in background without showing UI
  // Update suggestions tree view
}

function showMemoryDetail(memory: Memory) {
  const panel = vscode.window.createWebviewPanel(
    'mcpMemoryDetail',
    'Memory Detail',
    vscode.ViewColumn.Two,
    {}
  );

  panel.webview.html = `
    <html>
      <body>
        <h2>${memory.type}</h2>
        <p><strong>Project:</strong> ${memory.project || 'N/A'}</p>
        <p><strong>Importance:</strong> ${memory.importance_score.toFixed(2)}</p>
        <p><strong>Date:</strong> ${new Date(memory.timestamp).toLocaleString()}</p>
        <hr>
        <pre>${memory.content}</pre>
      </body>
    </html>
  `;
}

function generateRecallHtml(memories: Memory[]): string {
  const items = memories
    .map(
      (m) => `
    <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc;">
      <h3>${m.type}</h3>
      <p><strong>Project:</strong> ${m.project || 'N/A'}</p>
      <pre>${m.content.substring(0, 200)}...</pre>
    </div>
  `
    )
    .join('');

  return `
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
        </style>
      </head>
      <body>
        <h1>Recalled Memories</h1>
        ${items}
      </body>
    </html>
  `;
}

function generateDashboardHtml(data: any): string {
  return `
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          .stat { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
          .stat h3 { margin: 0; color: #666; }
          .stat p { font-size: 24px; font-weight: bold; margin: 5px 0 0 0; }
        </style>
      </head>
      <body>
        <h1>MCP Memory Dashboard</h1>
        <div class="stat">
          <h3>Total Memories</h3>
          <p>${data.total_memories || 0}</p>
        </div>
        <div class="stat">
          <h3>Total Entities</h3>
          <p>${data.total_entities || 0}</p>
        </div>
        <div class="stat">
          <h3>Avg Importance</h3>
          <p>${(data.avg_importance || 0).toFixed(2)}</p>
        </div>
      </body>
    </html>
  `;
}

class MemoryTreeProvider implements vscode.TreeDataProvider<MemoryItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<MemoryItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: MemoryItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: MemoryItem): Promise<MemoryItem[]> {
    if (!element) {
      // Root level - show recent memories
      try {
        const response = await axios.get(`${apiUrl}/memories`, { params: { limit: 10 } });
        const memories: Memory[] = response.data.memories;

        return memories.map(
          (m) =>
            new MemoryItem(
              m.content.substring(0, 40) + '...',
              m.type,
              vscode.TreeItemCollapsibleState.None
            )
        );
      } catch {
        return [];
      }
    }

    return [];
  }
}

class SuggestionsTreeProvider implements vscode.TreeDataProvider<SuggestionItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<
    SuggestionItem | undefined | null | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: SuggestionItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: SuggestionItem): Promise<SuggestionItem[]> {
    if (!element) {
      // Placeholder suggestions
      return [
        new SuggestionItem('Review authentication code', 'high'),
        new SuggestionItem('Complete TODO items', 'medium'),
      ];
    }

    return [];
  }
}

class MemoryItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly type: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
    this.tooltip = `Type: ${type}`;
    this.description = type;
  }
}

class SuggestionItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly priority: string
  ) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.tooltip = `Priority: ${priority}`;
    this.iconPath = new vscode.ThemeIcon('lightbulb');
  }
}

export function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}
