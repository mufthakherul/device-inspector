const modeEl = document.getElementById('mode');
const profileEl = document.getElementById('profile');
const outputDirEl = document.getElementById('outputDir');
const bundleDirEl = document.getElementById('bundleDir');
const runOutputEl = document.getElementById('runOutput');
const verifyOutputEl = document.getElementById('verifyOutput');
const reportSummaryEl = document.getElementById('reportSummary');
const artifactListEl = document.getElementById('artifactList');
const localOnlyEl = document.getElementById('localOnly');

function safeText(value) {
    if (value === null || value === undefined) return 'N/A';
    return String(value);
}

function setLog(el, message) {
    el.textContent = message;
}

document.getElementById('pickOutput').addEventListener('click', async () => {
    const picked = await window.inspectaDesktop.pickDirectory();
    if (!picked.canceled) {
        outputDirEl.value = picked.path;
        bundleDirEl.value = picked.path;
    }
});

document.getElementById('pickBundle').addEventListener('click', async () => {
    const picked = await window.inspectaDesktop.pickDirectory();
    if (!picked.canceled) {
        bundleDirEl.value = picked.path;
    }
});

localOnlyEl.addEventListener('change', async () => {
    const result = await window.inspectaDesktop.setLocalOnlyMode(localOnlyEl.checked);
    setLog(runOutputEl, `Local-only mode: ${result.enabled ? 'ENABLED' : 'DISABLED'}`);
});

document.getElementById('runBtn').addEventListener('click', async () => {
    const payload = {
        mode: modeEl.value,
        modesProfile: profileEl.value,
        outputDir: outputDirEl.value.trim()
    };

    setLog(runOutputEl, 'Running diagnostics...');
    const result = await window.inspectaDesktop.runInspection(payload);

    if (!result.ok) {
        setLog(runOutputEl, `FAILED (code=${safeText(result.code)})\n${safeText(result.stderr || result.error)}`);
        return;
    }

    bundleDirEl.value = result.outputDir || bundleDirEl.value;
    setLog(
        runOutputEl,
        `SUCCESS (code=${safeText(result.code)})\nCommand: ${safeText(result.command)}\n\n${safeText(result.stdout)}`
    );
});

document.getElementById('verifyBtn').addEventListener('click', async () => {
    const bundleDir = bundleDirEl.value.trim();
    setLog(verifyOutputEl, 'Verifying bundle...');
    const result = await window.inspectaDesktop.verifyBundle(bundleDir);

    if (!result.ok && !result.verify) {
        setLog(verifyOutputEl, `FAILED\n${safeText(result.stderr || result.error)}`);
        return;
    }

    if (result.verify) {
        setLog(verifyOutputEl, JSON.stringify(result.verify, null, 2));
        return;
    }

    setLog(verifyOutputEl, safeText(result.stdout));
});

document.getElementById('loadReportBtn').addEventListener('click', async () => {
    const bundleDir = bundleDirEl.value.trim();
    const reportPath = `${bundleDir}${bundleDir.endsWith('\\') || bundleDir.endsWith('/') ? '' : '/'}report.json`;

    const result = await window.inspectaDesktop.loadReport(reportPath);
    if (!result.ok) {
        reportSummaryEl.innerHTML = `<p class="error">${safeText(result.error)}</p>`;
        return;
    }

    const report = result.report || {};
    const summary = report.summary || {};
    const device = report.device || {};

    reportSummaryEl.innerHTML = `
    <p><strong>Vendor:</strong> ${safeText(device.vendor)}</p>
    <p><strong>Model:</strong> ${safeText(device.model)}</p>
    <p><strong>Serial:</strong> ${safeText(device.serial)}</p>
    <p><strong>Score:</strong> ${safeText(summary.overall_score)}/100</p>
    <p><strong>Grade:</strong> ${safeText(summary.grade)}</p>
    <p><strong>Recommendation:</strong> ${safeText(summary.recommendation)}</p>
    <p><strong>Generated:</strong> ${safeText(report.generated_at)}</p>
  `;
});

document.getElementById('loadArtifactsBtn').addEventListener('click', async () => {
    const bundleDir = bundleDirEl.value.trim();
    const result = await window.inspectaDesktop.listArtifacts(bundleDir);

    artifactListEl.innerHTML = '';
    if (!result.ok) {
        const li = document.createElement('li');
        li.textContent = `Error: ${safeText(result.error)}`;
        li.className = 'error';
        artifactListEl.appendChild(li);
        return;
    }

    for (const file of result.files || []) {
        const li = document.createElement('li');
        li.textContent = `${file.relative} (${file.size} bytes)`;
        artifactListEl.appendChild(li);
    }
});
