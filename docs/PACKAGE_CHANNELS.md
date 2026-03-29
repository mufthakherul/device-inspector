# Package Channel Metadata (Sprint 7)

This repository includes starter manifests/formulae/specs for native package channels:

- Winget: `packaging/winget/`
- Scoop: `packaging/scoop/inspecta-agent.json`
- Chocolatey: `packaging/chocolatey/`
- Homebrew: `packaging/homebrew/inspecta.rb`

## Release update checklist

When cutting a new release, update all channel metadata files with:

1. New version
2. New release URLs
3. SHA256 values from `dist/SHA256SUMS`

## Linux native artifacts

The release workflow now attempts to produce:

- `.deb`
- `.rpm`
- `.AppImage`

on Linux runners when required build tools are available.

## Verifying artifact checksums

After downloading release artifacts, verify integrity with `SHA256SUMS`.

### Windows (PowerShell)

- `Get-FileHash .\inspecta-0.1.0-windows.zip -Algorithm SHA256`

### macOS/Linux

- `sha256sum -c SHA256SUMS`

## Optional signature verification

You can additionally sign release files with GPG and publish `SHA256SUMS.asc`.

### Sign

- `gpg --armor --detach-sign SHA256SUMS`

### Verify

- `gpg --verify SHA256SUMS.asc SHA256SUMS`

> Maintainers should publish signing key fingerprints in release notes.
