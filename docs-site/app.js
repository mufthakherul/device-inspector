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

loadReleaseData();
