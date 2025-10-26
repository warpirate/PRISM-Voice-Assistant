/**
 * PRISM Electron Main Process
 * Manages application window, tray, and communication with backend
 */

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, nativeImage } = require('electron');

// Disable GPU acceleration to avoid Chrome/Electron GPU process crashes on certain drivers
app.disableHardwareAcceleration();
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');

let mainWindow = null;
let tray = null;
let backendProcess = null;
let wsServer = null;
let wsClient = null;

const WS_PORT = 9876;

// ============================================================================
// Application Lifecycle
// ============================================================================

app.whenReady().then(() => {
    createWindow();
    createTray();
    setupWebSocketServer();
    startBackend();
    registerShortcuts();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        cleanup();
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('will-quit', () => {
    cleanup();
});

// ============================================================================
// Window Management
// ============================================================================

function createWindow() {
    // Check if icon exists, use it if available
    const iconPath = path.join(__dirname, 'assets', 'icon.png');
    const windowOptions = {
        width: 400,
        height: 600,
        frame: false,
        transparent: true,
        resizable: false,
        alwaysOnTop: true,
        skipTaskbar: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        }
    };
    
    // Only add icon if file exists
    if (fs.existsSync(iconPath)) {
        windowOptions.icon = iconPath;
    }
    
    mainWindow = new BrowserWindow(windowOptions);

    mainWindow.loadFile('ui/index.html');

    // Position window at bottom-right corner
    const { screen } = require('electron');
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;
    
    mainWindow.setPosition(
        width - 420,
        height - 620
    );

    // Window events
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    mainWindow.on('blur', () => {
        // Optional: minimize to tray when focus is lost
        // mainWindow.hide();
    });

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
}

// ============================================================================
// System Tray
// ============================================================================

function createTray() {
    const trayIconPath = path.join(__dirname, 'assets', 'tray-icon.png');
    
    // Check if tray icon exists
    if (!fs.existsSync(trayIconPath)) {
        console.log('Tray icon not found, skipping tray creation');
        console.log('Add tray-icon.png to ui/assets/ to enable system tray');
        return;
    }
    
    tray = new Tray(trayIconPath);

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show PRISM',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                } else {
                    createWindow();
                }
            }
        },
        {
            label: 'Activate Voice',
            click: () => {
                sendToBackend({ type: 'activate_voice' });
            }
        },
        { type: 'separator' },
        {
            label: 'Settings',
            click: () => {
                // Open settings panel
                if (mainWindow) {
                    mainWindow.webContents.send('open-settings');
                }
            }
        },
        {
            label: 'Clear Conversation',
            click: () => {
                sendToBackend({ type: 'clear_conversation' });
            }
        },
        { type: 'separator' },
        {
            label: 'Quit PRISM',
            click: () => {
                cleanup();
                app.quit();
            }
        }
    ]);

    tray.setToolTip('PRISM - AI Assistant');
    tray.setContextMenu(contextMenu);

    // Double-click to show window
    tray.on('double-click', () => {
        if (mainWindow) {
            mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
    });
}

// ============================================================================
// Global Shortcuts
// ============================================================================

function registerShortcuts() {
    // Activation shortcut (Ctrl+Space)
    globalShortcut.register('CommandOrControl+Space', () => {
        sendToBackend({ type: 'activate_voice' });
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });

    // Toggle visibility (Ctrl+Shift+P)
    globalShortcut.register('CommandOrControl+Shift+P', () => {
        if (mainWindow) {
            mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
    });
}

// ============================================================================
// Backend Communication
// ============================================================================

function setupWebSocketServer() {
    wsServer = new WebSocket.Server({ port: WS_PORT });

    wsServer.on('connection', (ws) => {
        console.log('Backend connected via WebSocket');
        wsClient = ws;

        ws.on('message', (message) => {
            const data = JSON.parse(message.toString());
            handleBackendMessage(data);
        });

        ws.on('close', () => {
            console.log('Backend disconnected');
            wsClient = null;
            restartBackendIfNeeded();
        });

        ws.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    });

    console.log(`WebSocket server listening on port ${WS_PORT}`);
}

function startBackend() {
    if (backendProcess && !backendProcess.killed) return; // Already running
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    const backendScript = path.join(__dirname, '..', 'backend', 'main.py');

    backendProcess = spawn(pythonPath, [backendScript], {
        cwd: path.join(__dirname, '..'),
        env: { ...process.env }
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });

    console.log('Backend process started');
}

function sendToBackend(message) {
    if (wsClient && wsClient.readyState === WebSocket.OPEN) {
        wsClient.send(JSON.stringify(message));
        return true;
    }
    console.warn('Cannot send to backend - not connected');
    return false;
}

function handleBackendMessage(data) {
    if (!mainWindow) return;

    // Forward messages to renderer
    mainWindow.webContents.send('backend-message', data);

    // Handle specific message types
    switch (data.type) {
        case 'state_change':
            updateTrayIcon(data.state);
            break;
        
        case 'user_message':
        case 'assistant_message':
            // Show notification for important messages
            if (data.important) {
                showNotification(data.content);
            }
            break;
    }
}

function updateTrayIcon(state) {
    // Update tray icon based on state
    // Could change icon color or add indicator
    let tooltip = 'PRISM';
    
    switch (state) {
        case 'listening':
            tooltip = 'PRISM - Listening...';
            break;
        case 'processing':
            tooltip = 'PRISM - Processing...';
            break;
        case 'responding':
            tooltip = 'PRISM - Responding...';
            break;
        case 'error':
            tooltip = 'PRISM - Error';
            break;
    }
    
    if (tray) {
        tray.setToolTip(tooltip);
    }
}

function showNotification(message) {
    const { Notification } = require('electron');
    
    if (Notification.isSupported()) {
        const notificationOptions = {
            title: 'PRISM',
            body: message
        };
        
        // Add icon if it exists
        const iconPath = path.join(__dirname, 'assets', 'icon.png');
        if (fs.existsSync(iconPath)) {
            notificationOptions.icon = iconPath;
        }
        
        new Notification(notificationOptions).show();
    }
}

// ============================================================================
// IPC Handlers
// ============================================================================

ipcMain.on('send-to-backend', (event, message) => {
    sendToBackend(message);
});

ipcMain.on('minimize-window', () => {
    if (mainWindow) {
        mainWindow.hide();
    }
});

ipcMain.on('close-window', () => {
    cleanup();
    app.quit();
});

ipcMain.on('activate-voice', () => {
    sendToBackend({ type: 'activate_voice' });
});

ipcMain.on('send-text', (event, text) => {
    const ok = sendToBackend({ 
        type: 'process_text',
        text: text
    });
    if (!ok) {
        // Notify renderer so it can show an error and retry later
        event.sender.send('backend-message', { type: 'error', message: 'Backend not connected. Retrying…' });
        restartBackendIfNeeded();
    }
});

// ============================================================================
// Cleanup
// ============================================================================

function restartBackendIfNeeded() {
    // Attempt to restart if process exited or ws not connected
    const needRestart = !backendProcess || backendProcess.killed || backendProcess.exitCode !== null;
    if (needRestart) {
        console.log('Restarting backend…');
        startBackend();
    }
}

function cleanup() {
    console.log('Cleaning up...');

    // Unregister shortcuts
    globalShortcut.unregisterAll();

    // Close WebSocket
    if (wsServer) {
        wsServer.close();
    }

    // Kill backend process
    if (backendProcess) {
        backendProcess.kill();
    }
}
