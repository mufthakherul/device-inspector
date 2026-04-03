async function loadReleaseData() {
    const metaEl = document.getElementById('release-meta');
    const grid = document.getElementById('download-grid');

    if (!metaEl || !grid) {
        return;
    }

    try {
        const response = await fetch('./data/releases.json', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const payload = await response.json();
        const latest = payload.latest || {};
        const groups = payload.groups || {};

        metaEl.textContent = `Latest: ${latest.tag_name || 'N/A'} • Published: ${latest.published_at || 'N/A'}`;

        const entries = Object.entries(groups);
        if (entries.length === 0) {
            grid.innerHTML = '<p>No release assets available yet.</p>';
            return;
        }

        grid.innerHTML = '';
        for (const [group, assets] of entries) {
            const card = document.createElement('article');
            card.className = 'asset';
            const title = document.createElement('h3');
            title.textContent = group;
            card.appendChild(title);

            const list = document.createElement('ul');
            for (const asset of assets) {
                const item = document.createElement('li');
                const link = document.createElement('a');
                link.href = asset.browser_download_url;
                link.textContent = `${asset.name} (${Number(asset.size_bytes || 0).toLocaleString()} bytes)`;
                link.target = '_blank';
                link.rel = 'noreferrer noopener';
                item.appendChild(link);
                list.appendChild(item);
            }

            card.appendChild(list);
            grid.appendChild(card);
        }
    } catch (error) {
        metaEl.textContent = `Failed to load release metadata: ${error}`;
        grid.innerHTML = '';
    }
}

async function loadKpiSnapshot() {
    const target = document.getElementById('kpi-meta');
    if (!target) {
        return;
    }

    const source = target.dataset.src || '../data/kpi.json';

    try {
        const response = await fetch(source, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const payload = await response.json();
        const metrics = payload.metrics || {};

        target.innerHTML = [
            `<p><strong>Generated:</strong> ${payload.generated_at || 'N/A'}</p>`,
            `<p><strong>Tests Passed:</strong> ${metrics.tests_passed ?? 'N/A'}</p>`,
            `<p><strong>Coverage:</strong> ${metrics.coverage_percent ?? 'N/A'}%</p>`,
            `<p><strong>Release Green Rate:</strong> ${metrics.release_green_rate ?? 'N/A'}%</p>`,
            `<p><strong>Bundle Verify Rate:</strong> ${metrics.bundle_verify_rate ?? 'N/A'}%</p>`,
            `<p><strong>Probe Reliability:</strong> ${metrics.probe_reliability ?? 'N/A'}</p>`,
            `<p><strong>Probe Parity:</strong> ${metrics.probe_parity_index ?? 'N/A'}</p>`,
            `<p><strong>Confidence Score:</strong> ${metrics.confidence_score ?? 'N/A'}</p>`,
        ].join('');
    } catch (error) {
        target.textContent = `Failed to load KPI snapshot: ${error}`;
    }
}

async function loadDistributionManifest() {
    const target = document.getElementById('distribution-meta');
    if (!target) {
        return;
    }

    const source = target.dataset.src || '../data/distribution-manifest.json';

    try {
        const response = await fetch(source, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const payload = await response.json();
        const channels = Array.isArray(payload.channels) ? payload.channels : [];
        const available = channels.filter((channel) => channel.status === 'available').length;

        target.innerHTML = [
            `<p><strong>Generated:</strong> ${payload.generated_at || 'N/A'}</p>`,
            `<p><strong>Release Tag:</strong> ${payload.release?.tag_name ?? 'N/A'}</p>`,
            `<p><strong>Channels Available:</strong> ${available}/${channels.length}</p>`,
        ].join('');
    } catch (error) {
        target.textContent = `Failed to load distribution manifest: ${error}`;
    }
}

loadReleaseData();
loadKpiSnapshot();
loadDistributionManifest();
