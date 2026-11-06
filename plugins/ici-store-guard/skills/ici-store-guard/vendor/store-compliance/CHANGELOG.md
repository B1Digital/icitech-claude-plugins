# Changelog

Dates are when the rules were checked against the stores' own pages.

## 1.1.0 · 2026-11-05

### Added
- **Huawei AppGallery and HarmonyOS.** New `references/huawei.md` (review guidelines V52,
  2026-10-29). The scanner detects native ArkTS projects, Flutter for OpenHarmony (`ohos/`),
  React Native for OpenHarmony (`harmony/`) and uni-app (`harmony-configs/`), and checks
  `module.json5` permissions (reason, usedScene, restricted and deprecated permissions,
  location), build gates (bundleName, debug, SDK levels, signing, device types), HUAWEI ID
  login, consent before SDK init, OAID, the two personal-information lists, ads in widgets
  and ICP filing. Android apps on AppGallery get GMS-dependency and HMS-config checks.
- **Any agent.** `SKILL.md` follows the Agent Skills standard. Install instructions for
  Claude Code, Codex, Gemini CLI, Copilot, Cursor and others.
- Apple checks: iOS 13 deployment target and Xcode 26 floors, SDKs on Apple's privacy
  manifest list, invalid privacy manifests (ITMS-91056), ads in extensions, VPN.
- Google Play checks: 16 KB page size, Android 16 edge-to-edge, predictive back and
  orientation locks, R8 off, Restore Credentials, legacy Google Sign-In, SafetyNet,
  VpnService, sideload flavors, Play Billing 9, target API per form factor.
- Cross-store checks: age-rating inputs, age assurance APIs, loot-box odds, incentivised or
  custom review prompts, the new Sign in with Apple relay domain.
- Tests with fixture apps and a CI workflow.

### Changed
- Apple and Google references updated to 2026-11-05: new age-rating questions, Declared Age
  Range, US storefront link-outs, the 29 October 2026 Play policy update, precise location
  declarations, Play Billing 9 and the February 2027 quality thresholds.
- Random or anonymous chat as the main purpose is now reported as removal risk regardless of
  moderation, matching Apple 1.2.
- New banner.

## 1.0.0 · 2026-10-18

- First release: App Store and Google Play audits for Flutter, React Native, Expo and native
  apps.
