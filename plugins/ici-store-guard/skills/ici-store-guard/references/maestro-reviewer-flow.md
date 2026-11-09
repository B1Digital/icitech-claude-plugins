# Maestro reviewer flow

A repeatable smoke flow that covers what App Review checks first. Write it to the
scratch dir (`<scratch>/maestro/reviewer_smoke.yaml`), never into the audited repo —
offer to copy it into the repo (`.maestro/reviewer_smoke.yaml`) only if the user wants
to keep running it on every release.

Tested on a Flutter + Flame game (2026-11): passed end-to-end on an iPad Pro 13"
simulator; on an Android emulator it caught an empty paid shop (see "Android billing").

## Before writing it

1. Inspect the running app (`mcp__maestro__inspect_screen` or
   `maestro --device <id> hierarchy`) and list the labels you actually see, in the
   device's current language. Flutter exposes `Semantics` labels as `content-desc`
   (Android) / accessibility text (iOS); Maestro's `text:` matches both.
2. **Modal dialogs hide the screen behind them.** While a Flutter dialog/tutorial is
   open, the hierarchy shows only the dialog (e.g. one full-screen node + its
   "Continue" button). That is a modal barrier, not a broken tree — dismiss the dialog
   and inspect again before concluding labels are missing.
3. `text:` is a **full-string, case-insensitive regex**. Buttons that merge several
   texts read like `"Daily | gift | Claim"` or `"Free gems +5 | Watch a short video · 3 left today | Watch"`,
   so wrap partial matches as `".*Restore.*"`. Use alternation for locales:
   `"Ayarlar|Settings"`.
4. When a label appears more than once (header counters and a tab all reading "Shop"),
   pick by `index:` and note the duplicate label as an accessibility ÖNERİ.
5. `appId` = iOS bundle id / Android applicationId (often identical in Flutter apps;
   otherwise run with `-e APP_ID=...` per platform).

## Template

```yaml
appId: ${APP_ID}
name: Reviewer smoke
---
- launchApp:
    clearState: true            # fresh-install behaviour (first run, consent, ATT)
# Splash can take long on debug builds / cold emulators
- extendedWaitUntil:
    visible: "Continue|Devam|Got it|Anladım|Play|Oyna|Ask App Not to Track|Uygulama Beni Takip Etmesin"
    timeout: 60000
# iOS ATT / Android runtime permission: deny; the app must keep working (5.1.1(iv))
- runFlow:
    when:
      visible: "Ask App Not to Track|Uygulama Beni Takip Etmesin|Don.t Allow|İzin Verme"
    commands:
      - tapOn: "Ask App Not to Track|Uygulama Beni Takip Etmesin|Don.t Allow|İzin Verme"
- takeScreenshot: 01_first_run
# Walk past onboarding/tutorial dialogs as a reviewer would
- repeat:
    times: 12
    while:
      visible: "Continue|Devam|Got it|Anladım|Next|İleri"
    commands:
      - tapOn: "Continue|Devam|Got it|Anladım|Next|İleri"
      - waitForAnimationToEnd:
          timeout: 3000
- takeScreenshot: 02_home
# Shop / paywall: paid products must load (2.1(b)); compare amounts with store screenshots (2.3.7)
- tapOn:
    text: "Shop|Mağaza|Store|Premium"
    index: 2                    # adjust: which "Shop" is the tab
- extendedWaitUntil:
    visible: ".*(\\$|₺|€|£|TRY|USD)\\s?\\d+[.,]?\\d*.*"
    timeout: 15000
- takeScreenshot: 03_shop
# Settings: restore, privacy policy, account deletion if accounts exist
- tapOn: "Settings|Ayarlar"
- assertVisible: ".*(Restore|geri yükle).*"
- assertVisible: ".*(Privacy|Gizlilik).*"
- takeScreenshot: 04_settings
```

Adapt per app: login + demo account path, account-deletion path, the main user
journey (finish one level / create one item), and an offline run
(`setAirplaneMode: enabled` on Android; on iOS note it as manual).

## Running

```bash
maestro --device <ios-sim-udid> test <scratch>/maestro/reviewer_smoke.yaml -e APP_ID=<bundle>
maestro --device emulator-5554 test <scratch>/maestro/reviewer_smoke.yaml -e APP_ID=<applicationId>
```

- Install first: `xcrun simctl install <udid> <Runner.app>`; `adb -s emulator-5554 install -r <apk>`.
  **Always pass the device id** — a physical phone may also be on `adb`.
- Android AVD names: `emulator -list-avds` (Maestro's device list may show other names).
- If the Maestro MCP `run` fails with "Device server died", rerun the same YAML with
  the CLI; it reconnects.
- A failed step is a finding: name the step, attach the screenshot Maestro saved
  (`~/.maestro/tests/<timestamp>/`), and map it to the guideline in the comment above.

## Android billing on emulators

Play Billing needs a Google account signed in on a Play-Store image. Without it,
logcat shows `BILLING_UNAVAILABLE` (RevenueCat: `PurchaseNotAllowedError`) and no
products load. Record that as an environment limit, **but judge the app's fallback**:
if the paid section silently disappears (no "store unavailable / retry" message), that
is the same 2.1(b) risk a reviewer hits when billing hiccups — report it as RISK.
`adb -s <id> logcat -d | grep -iE "purchases|billing"` tells the two apart.
