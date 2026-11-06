# Runtime walkthrough (reviewer simulation)

Static scans miss what a reviewer sees in the first five minutes. Run this on the iOS
Simulator (`mcp__Claude_Code_iOS_Simulator__control`) and, if one is available, an
Android emulator. Take a screenshot at every step and attach the failing ones to the
report.

Build a **release-like** binary (`flutter build ios --simulator --release` is not
supported; use `--profile` or a debug build with `kDebugMode` banners off). Note which.

## Driving the simulator (lessons from the first run)

- Build into the repo's own `build/` (gitignored) with `flutter build ios --simulator --debug`,
  then `xcrun simctl uninstall <udid> <bundle>` for a true fresh install before `launch`.
- **Screenshots lag one step** behind taps during transitions/animations. After any
  navigation take two screenshots and trust the second; never conclude "button does
  the wrong thing" from a single post-tap frame.
- Tap coordinates are in device points; convert from the displayed screenshot size
  (`points = displayed_px × device_width_pt / displayed_width_px`).
- Game boards: tap-tap may not register during intro dialogs; use `swipe` (drag)
  with ~0.6 s duration.
- `xcrun simctl spawn <udid> log show --last 1m --predicate 'process == "Runner"'`
  shows crashes/exceptions without attaching a debugger.
- The simulator's region decides whether the UMP/GDPR form appears; outside the EEA
  it will not — say so, do not count it as verified.

## Steps (Apple guideline in brackets)

1. **Fresh install, cold start.** Delete the app first. Launch. No crash, no blank
   screen > 3 s, no debug banner, no placeholder text, no "lorem ipsum" [2.1, 2.3.3].
2. **Permission prompts.** Each system prompt appears only after a user action that
   needs it, and the purpose string matches what the app does [5.1.1].
   Tap "Don't Allow" on each: the app must keep working [5.1.1(iv)].
3. **Onboarding / sign-in.** If login exists: demo account in the review notes works;
   Sign in with Apple offered when any third-party social login is offered [4.8].
   Without login: the whole app is usable without forced registration [5.1.1(v)].
4. **Every tab and every primary button.** Tap each. Nothing dead, no "coming soon",
   no empty screen without an empty state [2.1, 2.2, 4.2].
5. **Paywall.** Price, period, auto-renew text, Terms + Privacy links visible on the
   paywall itself; Restore Purchases present; close button reachable [3.1.1, 3.1.2].
6. **Settings.** Privacy policy and terms links open; **account deletion** reachable
   in-app if accounts exist [5.1.1(v)]; support/contact link works [1.5].
7. **Offline.** Airplane mode, relaunch. Core flows work or show a clear error, no
   infinite spinner [2.1].
8. **Health / recovery content.** No medical claims ("cures", "treats"), crisis
   resources shown where self-harm or relapse is discussed [1.4.1, 1.1].
9. **AI features.** Disclosure + consent before sending user data to a third-party
   AI; report/flag on generated content [5.1.2(i), 1.2].
10. **Shop vs store screenshots.** Note every price/amount the running shop shows and
    compare with the store screenshots (2.3.7). Also note whether prices loaded at all.
11. **Dark Mode.** Switch the simulator to dark (`set_appearance dark`), relaunch:
    status-bar glyphs must stay legible over light game art (HIG; reviewers often use
    dark mode).
12. **iPad.** If the app is iPhone-only, confirm `UIDeviceFamily` excludes iPad;
    otherwise check layout on an iPad simulator — reviewers test on iPad [2.4.1].

A failure here is CRITICAL when a reviewer would hit it on the happy path,
IMPORTANT otherwise.
