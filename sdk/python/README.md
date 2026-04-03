# Inspecta Plugin SDK (Python)

This SDK skeleton provides a minimal contract-first starting point for third-party plugin development.

## Layout
- `inspecta_plugin_sdk/contracts.py` — typed plugin manifest/runtime contracts.
- `examples/health_plugin.py` — minimal example plugin implementation.

## Principles
- Deterministic outputs.
- Capability-declared behavior only.
- Surface-specific capability negotiation enforced by core runtime.
