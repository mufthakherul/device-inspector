# Inspecta Mobile (Sprint 9 MVP)

Flutter-based mobile companion for Android and iOS.

## MVP capabilities

- Open local `report.json` files for summary viewing
- Verify bundles using `artifacts/manifest.json` SHA256 checks
- Offline-first operation (no network dependency)
- Device pairing token UX via QR scan/local display

## Local setup

```bash
cd apps/mobile
flutter create . --platforms=android,ios
flutter pub get
flutter run
```

## Build artifacts

### Android

```bash
flutter build apk --release --dart-define=LOCAL_ONLY=true
flutter build appbundle --release --dart-define=LOCAL_ONLY=true
```

### iOS

Unsigned IPA:

```bash
flutter build ipa --release --no-codesign --dart-define=LOCAL_ONLY=true
```

Signed (when signing secrets/certificates are available in CI environment):

```bash
flutter build ipa --release --dart-define=LOCAL_ONLY=true
```

## Notes

CI workflows:

- `.github/workflows/build-mobile-android.yml`
- `.github/workflows/build-mobile-ios.yml`
