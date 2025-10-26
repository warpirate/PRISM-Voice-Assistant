const { app, BrowserWindow, Tray, Menu, ipcMain, globalShortcut } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let tray;
let pythonProcess;

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    transparent: true,
    frame: false,
    resizable: true,
    alwaysOnTop: true,
    skipTaskbar: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Prevent window from being closed, minimize to tray instead
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// Create system tray
function createTray() {
  const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show PRISM',
      click: () => {
        mainWindow.show();
      }
    },
    {
      label: 'Settings',
      click: () => {
        mainWindow.show();
        mainWindow.webContents.send('open-settings');
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('PRISM Voice Assistant');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

// Start Python backend
function startPythonBackend() {
  const pythonScript = path.join(__dirname, '..', 'backend', 'main.py');
  
  pythonProcess = spawn('python', [pythonScript], {
    cwd: path.join(__dirname, '..'),
    stdio: ['pipe', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    const message = data.toString().trim();
    console.log('Python:', message);
    
    try {
      const jsonData = JSON.parse(message);
      handlePythonMessage(jsonData);
    } catch (e) {
      // Not JSON, just log it
      console.log('Python output:', message);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('Python Error:', data.toString());
    if (mainWindow) {
      mainWindow.webContents.send('error', data.toString());
    }
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    if (code !== 0 && !app.isQuitting) {
      // Restart Python process if it crashes
      setTimeout(startPythonBackend, 2000);
    }
  });
}

// Handle messages from Python backend
function handlePythonMessage(data) {
  if (!mainWindow) return;

  switch (data.type) {
    case 'wake_word':
      mainWindow.webContents.send('wake-word-detected');
      break;
    case 'speech_recognized':
      mainWindow.webContents.send('speech-recognized', data.text);
      break;
    case 'response':
      mainWindow.webContents.send('response-ready', { text: data.text });
      break;
    case 'response_complete':
      mainWindow.webContents.send('response-complete');
      break;
    case 'status':
      mainWindow.webContents.send('update-status', { text: data.text, color: data.color });
      break;
    case 'error':
      mainWindow.webContents.send('error', data.message);
      break;
  }
}

// Send message to Python backend
function sendToPython(data) {
  if (pythonProcess && pythonProcess.stdin.writable) {
    pythonProcess.stdin.write(JSON.stringify(data) + '\n');
  }
}

// IPC Handlers
ipcMain.on('orb-clicked', () => {
  sendToPython({ type: 'manual_trigger' });
});

ipcMain.on('open-settings', () => {
  // TODO: Open settings window
  console.log('Settings requested');
});

ipcMain.on('text-query', (event, text) => {
  if (!text || !text.trim()) return;
  sendToPython({ type: 'text_query', text: String(text).trim() });
});

// App lifecycle
app.whenReady().then(() => {
  createWindow();
  createTray();
  startPythonBackend();

  // Register global shortcuts
  globalShortcut.register('CommandOrControl+Shift+P', () => {
    mainWindow.show();
    sendToPython({ type: 'manual_trigger' });
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
  
  // Kill Python process
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  // Unregister shortcuts
  globalShortcut.unregisterAll();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});
