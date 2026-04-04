# Mobile Secure Key & Pairing Material Plan (P3)

Last updated: 2026-04-04

## Objective

Define a platform-specific secure key/material handling strategy for offline pairing and evidence verification in the mobile companion.

## Security requirements

- Pairing tokens must be offline-first and short-lived (TTL <= 10 minutes).
- Pairing material rotation is mandatory between sessions.
- Integrity binding must be enabled (hash/signature metadata required).
- No cloud key escrow dependency for baseline operation.

## Platform key storage strategy

### Android (Kotlin bridge track)

- Store long-lived verifier secrets in Android Keystore.
- Use hardware-backed keys when available.
- Restrict key export (non-exportable aliases only).
- Enforce biometric/pin-gated access for privileged actions where UX allows.

### iOS (Swift bridge track)

- Store verifier secrets in Keychain with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` baseline.
- Use Secure Enclave-backed keys when available.
- Disable key migration for device-bound trust material.

## Operational plan

1. Generate pairing token in app (QR/file/LAN modes).
2. Bind token to issuance time + TTL + integrity metadata.
3. Persist only minimal session metadata; rotate on completion/failure.
4. Revoke stale pairing material automatically.

## Audit and compliance hooks

- Emit local pairing session audit entries (timestamp, mode, status).
- Keep no raw personal identifiers in pairing metadata.
- Maintain deterministic validation outcomes for forensics.

## Next implementation checkpoints

- Add Kotlin secure-storage bridge interface contract.
- Add Swift secure-storage bridge interface contract.
- Add integration tests for token TTL and rotation enforcement.
