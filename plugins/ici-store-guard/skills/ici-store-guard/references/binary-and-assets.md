# Built binary + store assets checklist

Distilled from a bake-off on a Flutter + Flame game (2026-11-06) (appstore-preflight method, re-done with
standard tools). Every item below found something real at least once, or is a
mechanical upload blocker. Mark each PASS / FLAG / BLOCK / UNKNOWN with evidence path.

## iOS (unzip the IPA into scratch, never into the repo)

1. **Version provenance** — `CFBundleShortVersionString`/`CFBundleVersion` match
   `pubspec.yaml`; IPA mtime vs `git log -1`; `git status` dirty? An uncommitted
   version bump = build not reproducible (FLAG).
2. **Merged Info.plist** (`plutil -p Payload/*.app/Info.plist`):
   `ITSAppUsesNonExemptEncryption`, every `*UsageDescription` used vs. present,
   `NSUserTrackingUsageDescription` + localized `*.lproj/InfoPlist.strings`,
   `GADApplicationIdentifier` (not test `ca-app-pub-3940256099942544`),
   `SKAdNetworkItems` count, `UIDeviceFamily`, orientations per idiom,
   `UIRequiresFullScreen` (deprecated since iPadOS 26 — FLAG if iPad is supported and
   layout is portrait-only), launch storyboard, `MinimumOSVersion`, SDK/Xcode build.
   iPad without UIRequiresFullScreen must support all 4 orientations (ITMS-90474).
3. **Privacy manifests** — app-level `PrivacyInfo.xcprivacy` present? List every
   embedded framework/bundle and whether it carries one; `nm -u Runner | grep` for
   required-reason APIs (UserDefaults, file timestamp, disk space, system boot time)
   and confirm each category is declared somewhere. With Flutter SPM, SDK code is
   statically merged into `Runner`, so judge coverage in aggregate, not per stub.
   `NSPrivacyTracking` must be true if the app requests ATT.
4. **Entitlements** — `codesign -d --entitlements :- Payload/*.app`: `get-task-allow`
   false, no `aps-environment` without push code, no Apple-gated entitlements unused.
   Provisioning profile type (App Store) and expiry (`security cms -D -i embedded.mobileprovision`).
5. **Ad IDs in the AOT snapshot** — `strings App.framework/App | grep ca-app-pub`:
   no test IDs in release.
6. **Icon** — 1024 marketing icon present in `Assets.car` (`assetutil --info`), source
   PNG has no alpha (`sips -g hasAlpha`).

## Android (AAB)

- `bundletool dump manifest` (or the merged release manifest under `build/`):
  `debuggable`, `usesCleartextTraffic`, permissions actually merged (AD_ID,
  FOREGROUND_SERVICE without type), targetSdk, versionCode vs pubspec.
- Signing cert is the upload key, not debug (`keytool -printcert -jarfile`).
- Native libs 16 KB aligned (`zipalign -c -P 16` or LOAD segment alignment).

## Store assets (fastlane/, store_shots/, aso/)

1. **Screenshots show the real app, with real data.** Open the shop/paywall panels
   and compare prices, product names and amounts to what the running app shows
   (Phase 4) and to the IAP config. Screenshots rendered from widget tests often use
   a fake store that returns one price for everything — that is a 2.3.7 rejection
   (seen in practice: every pack shown as "$1.99"). Check `test/**/fakes*` if prices look
   uniform.
2. Sizes/alpha: iPhone 6.9" 1320×2868 (or 6.5" 1284×2778), iPad 13" 2064×2752, no alpha,
   ≤10 per device per locale, every metadata locale has screenshots.
3. **Metadata locales vs binary languages** (`CFBundleLocalizations`, l10n files):
   listing in 50 languages for a 5-language app → FLAG (2.3 / reviews), worst for RTL.
4. `release_notes.txt` filled on a 1.0 version → ASC rejects/ignores (FLAG).
5. Description claims (level counts, "remove ads") match content and IAP behaviour.
6. Privacy/support URLs present; fetch them only if the user allows network.
