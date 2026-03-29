# Release checklist

## 1) Pre-release

1. Run tests and ensure CI is green.
2. Bump version in `agent/__init__.py` and `pyproject.toml`.
3. Update package channel metadata in:
	- `packaging/winget/`
	- `packaging/scoop/inspecta-agent.json`
	- `packaging/chocolatey/`
	- `packaging/homebrew/inspecta.rb`

## 2) Tag and publish

1. Create and push tag (`vX.Y.Z`).
2. `build-release.yml` will build:
	- Windows/macOS/Linux standalone `.zip`
	- Linux native `.deb`, `.rpm`, `.AppImage` (where tooling is available)
	- Python `sdist` and `wheel`
	- `SHA256SUMS`
3. `publish-pypi.yml` publishes the Python package to PyPI via trusted publishing.

## 3) Integrity verification

1. Download release assets and `SHA256SUMS`.
2. Verify hashes:
	- Windows: `Get-FileHash <file> -Algorithm SHA256`
	- Linux/macOS: `sha256sum -c SHA256SUMS`

## 4) Optional detached signatures

To provide stronger provenance guarantees, sign `SHA256SUMS` with GPG:

- Sign: `gpg --armor --detach-sign SHA256SUMS`
- Verify: `gpg --verify SHA256SUMS.asc SHA256SUMS`

Publish key fingerprint and verification instructions in release notes.
