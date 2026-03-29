# Platform Capability Matrix & Support Policy

_Last updated: 2026-03-29_

| Platform | Primary Outputs | CI Workflow | Support Level | Notes |
|---|---|---|---|---|
| Windows | `.exe`, `.msix` | `build-desktop-apps.yml`, `build-release.yml` | stable | CLI + desktop packaging active |
| macOS | `.dmg`, `.pkg` | `build-desktop-apps.yml`, `build-release.yml` | stable | Desktop installer lane active |
| Linux | `.AppImage`, `.deb`, `.rpm` | `build-desktop-apps.yml`, `build-release.yml` | stable | CLI + desktop packaging active |
| Android | `.apk`, `.aab` | `build-mobile-android.yml` | stable | Unsigned build guaranteed; signed lane optional with secrets |
| iOS | `.ipa` | `build-mobile-ios.yml` | stable | Unsigned build guaranteed; signed lane optional with secrets |
| HarmonyOS | `.hap` | `build-harmonyos.yml` | scaffold | Toolchain probe + scaffold artifacts until CI toolchain is provisioned |

## Support policy

- **stable**: automated in CI and expected to be release-ready.
- **beta**: automated but still under validation/hardening.
- **scaffold**: workflow and architecture are present; production packaging depends on external toolchain provisioning.

## Promotion criteria

A platform can move from `scaffold` → `beta` → `stable` when all are true:

1. CI reliably produces target artifacts.
2. Signing/release flow is documented and repeatable.
3. Offline verification behavior is validated on representative real devices.
4. Release rollback guidance is documented.
