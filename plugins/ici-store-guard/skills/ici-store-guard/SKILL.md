---
name: ici-store-guard
description: One-shot pre-submission audit for Flutter / mobile apps before sending to Apple App Store and Google Play. Runs three vetted auditors (store-compliance scanner, devsemih App Store + Play review, Google's official play-policy-insights) plus a built-binary/store-screenshot check and an iOS Simulator (iPad) reviewer walkthrough, de-duplicates and verifies findings, and produces one GO / NO-GO report with fixes, console manual checks and a draft App Review Notes text. Use when the user wants to check an app before release, asks "will this get rejected", "mağazaya göndermeden kontrol", "store preflight", "yayın öncesi denetim", "Apple/Google red riski", or before any TestFlight / production submission. After a rejection has already arrived, use app-rejection-recovery instead.
argument-hint: "[path] [--ios|--android] [--no-runtime] [--quick] [--out <dir>]"
---

# ici-store-guard

Single entry point that runs every store-review auditor we trust and merges the
results into **one** report. The vendored auditors live in `vendor/` (see
`vendor/VENDOR.md` for provenance). `<skill>` below means the directory holding this
file — resolve it to its real path (the plugin's `skills/ici-store-guard` folder,
e.g. under `~/.claude/plugins/`).

Write the report and all chat output in the user's language (Turkish if the user
writes Turkish). Guideline / policy names stay as the stores write them.

## Arguments

| Arg | Meaning |
|---|---|
| `[path]` | App repo. Default: current directory |
| `--ios` / `--android` | Limit to one store. Default: both platforms present in the repo |
| `--no-runtime` | Skip the simulator walkthrough (Phase 4, on by default) |
| `--quick` | Phase 1 scanner + Phase 3 verification only (≈2 min, no subagents, no runtime) |
| `--out <dir>` | Report directory. Default: `~/store-guard-reports/<app>/` |

## Hard rules

- **Never write into the audited repo** during the audit. All scratch files go to
  `<scratch>` = the session scratchpad if there is one, else `mktemp -d`.
- Google's orchestrator creates `.scratch/` under its **current working directory** —
  always `cd <scratch>` before running it.
- Do not change app code unless the user asks after the report.
- A scanner hit is a lead, not a finding. CRITICAL / IMPORTANT need a cited
  `file:line` you have read yourself (evidentiary standard in
  `vendor/store-compliance/SKILL.md` §3 applies to every source).
- Subagents run at most 3 at a time.

## Phase 0 — Context (main agent, fast)

1. Detect: Flutter? (`pubspec.yaml`), `ios/` and `android/` present, bundle id
   (`ios/Runner.xcodeproj/project.pbxproj` → `PRODUCT_BUNDLE_IDENTIFIER`), Android
   `applicationId` (`android/app/build.gradle(.kts)`), version, `targetSdk`.
2. Read the project's own `CLAUDE.md` / README for what the app does (category,
   login?, IAP?, AI?, UGC?, health claims?). One paragraph, kept for subagent briefs.
3. Rules freshness: the vendored rule dates are in each vendor SKILL.md
   (`rules-as-of`, "Guidelines version"). If the newest is > 45 days old, fetch
   https://developer.apple.com/news/ and
   https://support.google.com/googleplay/android-developer/table/12921780 and list
   anything newer under "Kural değişiklikleri" in the report.

## Phase 1 — Deterministic scan (main agent)

```bash
python3 -I <skill>/vendor/store-compliance/scripts/scan.py <repo> --json <scratch>/scan.json
```

Read `scan.json` (`facts` + `findings`). This is the shared fact base; pass its path
to every subagent. With `--quick`, skip to Phase 3.

## Phase 2 — Parallel audits (subagents, one message, ≤3)

Spawn these with the Agent tool (`general-purpose`), each given: repo path, the
Phase 0 paragraph, `<scratch>/scan.json`, its output path, and "write findings to
the file, reply only DONE". Skip the ones whose platform is excluded.

| Agent | Instructions file | Output |
|---|---|---|
| **apple** | `<skill>/vendor/appstore-review-skill/skills/appstore-review/SKILL.md` (its `../../references/guidelines-summary.md` is relative to that file) | `<scratch>/apple.md` |
| **play** | `<skill>/vendor/appstore-review-skill/skills/playstore-review/SKILL.md` | `<scratch>/play.md` |
| **google-official** | `<skill>/vendor/play-policy-insights/SKILL.md` — tell it: `repo_root=<skill>/vendor/play-policy-insights`, `app_dir=<repo>`, **cd to `<scratch>` before `orchestrator.py init`**, run its scripts with `python3 -E -s` (**not** `-I`: `-I` drops the script dir from `sys.path` and it cannot import its own `scanner` module), the Play package name is the Android `applicationId` from Phase 0 (not the Dart package name — correct it if the report looked up the wrong one), use **Mode B (sequential)**, copy the final `compliance_report.md` to `<scratch>/google.md`, and also list any Data safety items that appear only in critic outputs | `<scratch>/google.md` |

Tell the apple/play agents to ignore the vendored skills' own "Output Format"
location rules and write only to the given output path.

If the Google orchestrator fails (it is strict: fail-fast), record "Google
play-policy-insights çalışmadı: <reason>" and continue — do not block the report.

## Phase 2b — Built binary + store assets (one more subagent, same batch rules)

Source scans cannot see what actually uploads. Find the newest built artefact
(`build/ios/ipa/*.ipa`, `build/ios/archive/*.xcarchive`, `~/Library/Developer/Xcode/Archives`,
`build/app/outputs/bundle/release/*.aab`). If none exists, say so in "Çalışmayan
denetimler" and do not build one unasked. Brief the agent with
`<skill>/references/binary-and-assets.md` and output `<scratch>/binary.md`. Use only
standard tools (unzip, plutil, codesign, security cms, sips, assetutil, nm, strings,
bundletool if present) — never run third-party scripts.

## Phase 3 — Merge and verify (main agent)

1. Collect findings from `scan.json`, `apple.md`, `play.md`, `google.md`.
2. **De-duplicate**: same store + same rule + same file (or same missing artifact)
   = one finding. Keep the clearest evidence; list which auditors raised it
   (`kaynak: scanner, apple, google`) — agreement across sources raises confidence.
3. **Verify** every CRITICAL and IMPORTANT by reading the cited lines (parallel
   reads). Confirm / downgrade (say why) / drop. Report the dropped count in one line.
4. **Cross-platform parity** (cross-platform apps; checks no single-store auditor makes):
   - *Declaration drift* — every data-collecting SDK in `pubspec.yaml`/`package.json` is
     declared on **both** the iOS App Privacy answers and the Play Data safety form,
     with the same linked/tracking stance (e.g. `fastlane/app_privacy_details.json` vs.
     the Data safety list you derive). A one-sided declaration is RISK.
   - *Behavioural drift* — grep `kReleaseMode`, `kDebugMode`, `__DEV__`,
     `Platform.isIOS/isAndroid`, `defaultTargetPlatform`: does release build or one
     platform change ads, prices, paywalls, permissions or features? Anything that only
     appears in release, or only on one store, must be in that store's review notes.
   - *Deep-link parity* — if the app uses deep links: iOS associated domains
     (`Runner.entitlements`, `apple-app-site-association`) vs. Android
     `intent-filter autoVerify` + `assetlinks.json`; one working and one not is RISK.
   - *Parity matrix* — in the report, a short table: feature / permission / IAP /
     login / ads × iOS × Android, flagging anything present on only one side.
5. Normalise levels: **BLOCK** (will be rejected / update blocked),
   **RISK** (likely rejection, reviewer-dependent), **ÖNERİ** (best practice),
   **MANUEL** (lives in App Store Connect / Play Console, cannot be seen in code).

## Phase 4 — Runtime walkthrough (default ON; skip with `--no-runtime`, `--quick` or no simulator)

~65% of Apple rejections are Guideline 2 (Performance / 2.1 completeness) per Apple's
2025 Transparency Report — things only a running app shows. So this phase is not
optional by default. Follow `<skill>/references/runtime-walkthrough.md` on an **iPad**
simulator first (reviewers use iPads), fresh install. Runtime results also
**confirm or refute** static RISK items — update their level (e.g. "ATT prompt may not
show" → refuted if it showed on a fresh install). Failures become findings with a
screenshot path instead of `file:line`.

**Optional tools — use them when present, never require them:**

| Tool | How to detect | What it adds |
|---|---|---|
| **Maestro** (`maestro` CLI / `maestro` MCP server) | `which maestro`, or `mcp__maestro__*` tools | Drives iOS sim **and Android emulator** by accessibility labels instead of pixel coordinates; writes a repeatable reviewer flow. See `references/maestro-reviewer-flow.md`. |
| **Dart & Flutter MCP** (`dart mcp-server`, tools `mcp__dart__*`) | `mcp__dart__get_runtime_errors` available | During the walkthrough, `launch_app` / `dtd` connect + `get_runtime_errors` catch Flutter errors that do not crash (RenderFlex overflow, null errors) but leave blank or broken widgets a reviewer reports under 2.1. Also `analyze_files` for a quick analyzer pass. |
| Built-in iOS Simulator tool | `mcp__Claude_Code_iOS_Simulator__control` | Live panel the user can watch; screenshots. Fallback driver when Maestro is absent. |

With Maestro available, run the walkthrough on **both** an iPad simulator and an
Android emulator (`maestro list-devices`; boot one with `emulator -avd <name>` if none
is running). Without it, iOS only — say so under "Çalışmayan denetimler".
Always target devices by explicit id (`--device`, `adb -s`): a physical phone may also
be connected, and installing or running flows on it is not part of an audit.

## Phase 5 — Report

One file: `<out>/store-guard-<app>-<YYYY-MM-DD>.md`, structure:

```markdown
# Store Guard — <App> <version> (<date>)
**Karar: GO / NO-GO**  (NO-GO if any BLOCK)
| Mağaza | BLOCK | RISK | ÖNERİ | MANUEL |

## BLOCK
### [Apple 5.1.1(v)] <başlık>
- **Ne:** tek cümle
- **Kanıt:** `path:line`
- **Risk:** red / kaldırma / güncelleme engeli
- **Düzeltme:** somut kod veya konsol adımı (kısa snippet)
- **Kaynak:** scanner · apple · google

## RISK
## ÖNERİ
## MANUEL kontroller (App Store Connect / Play Console)
- App Privacy & Data safety formları scan.json `sdk_categories` ile birebir mi
- Yaş derecelendirmesi, kategori, ekran görüntüleri gerçek UI'ı mı gösteriyor
- Demo hesap / review notes, iletişim bilgisi
## App Review Notes taslağı
<İngilizce, reviewer'a yapıştırılacak metin: uygulama ne yapar, giriş gerekiyor mu
(demo hesap), IAP nasıl test edilir, hassas özellikler neden var (AI, sağlık
içeriği, izinler), offline davranış.>
## Kural değişiklikleri (varsa)
## Çalışmayan denetimler (varsa)
```

In chat: the verdict, the count table, the top 3 BLOCK/RISK items, and the report
path. Details stay in the file.

## Phase 6 — After the report

- If the user asks to fix: one logical change per commit, follow the repo's own
  rules (CLAUDE.md), then re-run Phase 1 to show the finding is gone.
- A rejection already received → hand over to the `app-rejection-recovery` skill
  with this report as context.
