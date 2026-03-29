const { app, BrowserWindow, dialog, ipcMain, session } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let localOnlyMode = true;

function guessWorkspaceRoot() {
    return path.resolve(__dirname, '..', '..');
}

function loadCapabilityMatrix() {
    const root = guessWorkspaceRoot();
    const matrixPath = path.join(root, 'schemas', 'capability-matrix-1.0.0.json');
    if (!fs.existsSync(matrixPath)) {
        return { ok: false, error: 'Capability matrix not found.' };
    }

    try {
        const payload = JSON.parse(fs.readFileSync(matrixPath, 'utf-8'));
        return {
            ok: true,
            matrixVersion: payload.matrix_version,
            desktop: payload.surfaces?.desktop || null
        };
    } catch (error) {
        return { ok: false, error: error.message };
    }
}

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 860,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

function setupNetworkPolicy() {
    session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
        if (!localOnlyMode) {
            callback({ cancel: false });
            return;
        }

        const url = details.url || '';
        const blocked = url.startsWith('http://') || url.startsWith('https://') || url.startsWith('ws://') || url.startsWith('wss://');
        callback({ cancel: blocked });
    });
}

function choosePythonCommand() {
    const candidates = [];
    if (process.env.INSPECTA_PYTHON) {
        candidates.push([process.env.INSPECTA_PYTHON, []]);
    }
    candidates.push(['python', []]);
    if (process.platform === 'win32') {
        candidates.push(['py', ['-3']]);
    }
    return candidates;
}

function runCommand(command, args, cwd) {
    return new Promise((resolve) => {
        const child = spawn(command, args, { cwd, shell: false });
        let stdout = '';
        let stderr = '';

        child.stdout.on('data', (chunk) => {
            stdout += chunk.toString();
        });
        child.stderr.on('data', (chunk) => {
            stderr += chunk.toString();
        });

        child.on('error', (error) => {
            resolve({ ok: false, code: -1, stdout, stderr: `${stderr}\n${error.message}`.trim() });
        });

        child.on('close', (code) => {
            resolve({ ok: code === 0, code, stdout, stderr });
        });
    });
}

async function runAgentCommand(agentArgs, cwd) {
    const candidates = choosePythonCommand();
    let lastResult = { ok: false, code: -1, stdout: '', stderr: 'No Python interpreter candidates available.' };

    for (const [exe, preArgs] of candidates) {
        const result = await runCommand(exe, [...preArgs, '-m', 'agent.cli', ...agentArgs], cwd);
        if (result.ok || result.code !== -1) {
            return { ...result, command: [exe, ...preArgs, '-m', 'agent.cli', ...agentArgs].join(' ') };
        }
        lastResult = result;
    }

    return lastResult;
}

ipcMain.handle('ui:pick-directory', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory', 'createDirectory'] });
    if (result.canceled || result.filePaths.length === 0) {
        return { canceled: true };
    }
    return { canceled: false, path: result.filePaths[0] };
});

ipcMain.handle('ui:set-local-only-mode', async (_event, enabled) => {
    localOnlyMode = Boolean(enabled);
    return { enabled: localOnlyMode };
});

ipcMain.handle('ui:get-capabilities', async () => {
    return loadCapabilityMatrix();
});

ipcMain.handle('ui:run-inspection', async (_event, payload) => {
    const cwd = guessWorkspaceRoot();
    const mode = payload?.mode === 'full' ? 'full' : 'quick';
    const profile = ['balanced', 'deep', 'forensic'].includes(payload?.modesProfile) ? payload.modesProfile : 'balanced';
    const output = payload?.outputDir;
    if (!output) {
        return { ok: false, error: 'Output directory is required.' };
    }

    const args = ['run', '--mode', mode, '--output', output, '--no-auto-open'];
    if (mode === 'full') {
        args.push('--modes-profile', profile);
    }

    const result = await runAgentCommand(args, cwd);
    return {
        ...result,
        outputDir: output,
        reportPath: path.join(output, 'report.json')
    };
});

ipcMain.handle('ui:verify-bundle', async (_event, bundleDir) => {
    const cwd = guessWorkspaceRoot();
    if (!bundleDir) {
        return { ok: false, error: 'Bundle directory is required.' };
    }

    const args = ['verify', bundleDir, '--json'];
    const result = await runAgentCommand(args, cwd);

    if (!result.stdout) {
        return result;
    }

    try {
        const parsed = JSON.parse(result.stdout);
        return { ...result, verify: parsed };
    } catch {
        return { ...result, verify: null };
    }
});

ipcMain.handle('ui:load-report', async (_event, reportPath) => {
    if (!reportPath || !fs.existsSync(reportPath)) {
        return { ok: false, error: 'report.json not found.' };
    }

    try {
        const text = fs.readFileSync(reportPath, 'utf-8');
        const data = JSON.parse(text);
        return { ok: true, report: data };
    } catch (error) {
        return { ok: false, error: error.message };
    }
});

ipcMain.handle('ui:list-artifacts', async (_event, bundleDir) => {
    if (!bundleDir || !fs.existsSync(bundleDir)) {
        return { ok: false, error: 'Bundle directory not found.' };
    }

    const files = [];
    function walk(dir) {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
            const full = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                walk(full);
                continue;
            }
            files.push({
                name: entry.name,
                path: full,
                relative: path.relative(bundleDir, full),
                size: fs.statSync(full).size
            });
        }
    }

    walk(bundleDir);
    files.sort((a, b) => a.relative.localeCompare(b.relative));
    return { ok: true, files };
});

app.whenReady().then(() => {
    setupNetworkPolicy();
    createWindow();

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
