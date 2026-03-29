const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('inspectaDesktop', {
  pickDirectory: () => ipcRenderer.invoke('ui:pick-directory'),
  setLocalOnlyMode: (enabled) => ipcRenderer.invoke('ui:set-local-only-mode', enabled),
  runInspection: (payload) => ipcRenderer.invoke('ui:run-inspection', payload),
  verifyBundle: (bundleDir) => ipcRenderer.invoke('ui:verify-bundle', bundleDir),
  loadReport: (reportPath) => ipcRenderer.invoke('ui:load-report', reportPath),
  listArtifacts: (bundleDir) => ipcRenderer.invoke('ui:list-artifacts', bundleDir)
});
