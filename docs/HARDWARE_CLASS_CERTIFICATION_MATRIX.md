# Hardware Class Certification Matrix (P6)

Last updated: 2026-04-04

| Class ID | Target Devices | Support Level | Recommended Mode | Validation Pack |
|---|---|---|---|---|
| `laptop-desktop` | Laptops, desktops, workstations | stable | full | `core-laptop-desktop` |
| `tablet-mobile` | Android/iOS tablets | beta | quick | `tablet-mobile-baseline` |
| `arm-rpi-linux` | Raspberry Pi / ARM Linux edge hosts | beta | quick | `arm-rpi-linux-baseline` |
| `edge-mini-pc` | Mini-PC / IoT edge devices | beta | full | `edge-mini-pc-baseline` |
| `fireos-companion` | Amazon Fire OS companion lane | scaffold | quick | `fireos-companion-mvp` |

## Certification policy

- `stable`: release-grade and validated in recurring CI/device checks.
- `beta`: feature-complete but still maturing across wider hardware variety.
- `scaffold`: architecture and validation assets are present; production guarantees pending.

## Validation requirements

1. Profile pack exists and passes schema/policy validation.
2. Assigned validation pack is deterministic and offline-compatible.
3. Device-class mapping and summary output are emitted in report composition.
