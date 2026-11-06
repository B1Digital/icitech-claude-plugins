---
name: store-compliance
description: Audits mobile app repositories (Flutter, React Native/Expo, native iOS/Android, HarmonyOS/ArkTS) against the current Apple App Review Guidelines, Google Play Developer Policies and Huawei AppGallery review rules, and reports each violation with evidence, the store risk and a concrete fix. Use when the user asks whether an app will pass App Store, Play or AppGallery review, wants a pre-submission or compliance audit, asks about new or changed review guidelines or policy deadlines, received a rejection, or wants to scan one or many mobile repos for store-policy risks (also in Turkish, e.g. "mağaza uyumu", "review guideline tarama", "reddedilme riski").
license: MIT
compatibility: Works with any agent that reads Agent Skills (SKILL.md). Needs python3 (3.9+). gh only for scanning a GitHub repo that is not cloned. Web access to check for newer store rules.
allowed-tools: Read Grep Glob
metadata:
  version: "1.1.0"
  rules-as-of: "2026-11-05"
---

# store-compliance

The input is the user's request, plus any arguments given when the skill is
invoked by name (a path, `owner/repo`, a folder of repos or `all`, and
`--lang`).

Scan mobile repos for things that get an app rejected, removed or blocked from
updating on the App Store, Google Play and Huawei AppGallery (HarmonyOS apps and
Android APKs). Every finding must carry evidence
(`file:line`), the guideline or policy it breaks, what the store does about it,
and how to fix it.

The scanner gathers facts. **You** decide. A scanner hit is a lead until you
have read the cited code.

## 0. Check the rules are current

The rules in `references/` are dated (`rules-as-of` above). The stores change
them several times a year.

- If `rules-as-of` is more than 45 days old, or the user mentions a change you
  do not see in the references, fetch these two pages first and note anything
  newer in the report under "Rule changes since the references":
  - https://developer.apple.com/news/ (entries titled "Updated App Review Guidelines…")
  - https://support.google.com/googleplay/android-developer/table/12921780 (Play policy deadlines)
  - https://developer.huawei.com/consumer/cn/doc/app/50104 (AppGallery 应用审核指南, check the version number)
- Do not silently edit the references. Tell the user what changed and offer to
  update them.

## 1. Resolve the targets

| Argument | Do |
|---|---|
| empty | the current directory, if it holds a mobile app |
| a path | that repo. Monorepos are fine: the scanner finds every app dir inside |
| `owner/repo` | `gh repo clone owner/repo <scratch>/<repo> -- --depth 1`, then scan the clone |
| a directory of repos, or `all` | `python3 -I <skill>/scripts/scan.py --find <dir…>` lists app dirs (linked git worktrees are skipped). Show the list and confirm before scanning more than 10 |

Use a scratch directory for clones and JSON (the session scratchpad if the
agent has one, otherwise a temp dir). Never write into the audited repo.

## 2. Run the scanner

`<skill>` is the directory that holds this SKILL.md. Where it lives depends on
the agent (for example `~/.claude/skills/store-compliance` or
`~/.agents/skills/store-compliance`). Use the real path, not a guess.

```bash
python3 -I <skill>/scripts/scan.py <repo> --json <scratch>/<repo>.json
```

It is stdlib-only and read-only. The JSON holds, per app:

- `facts`: stack, platforms, SDK categories (ads, tracking, login, IAP, AI,
  UGC, remote config, code push…), Info.plist purpose strings, privacy manifest,
  Android permissions, resolved `targetSdk`/`minSdk`, Play Billing version,
  Android Gradle Plugin, background modes, and for HarmonyOS `facts.harmonyos`
  (bundleName, SDK levels, declared permissions, modules).
- `findings`: `id`, `platform` (`ios`, `android`, `harmonyos`, `appgallery`
  or `both` for cross-store rules), `level` (CRITICAL / IMPORTANT /
  SUGGESTION), `refs`, `title`, `evidence`.

ID prefixes: `X-` cross-store, `IOS-`, `AND-`, `EXPO-`, `HOS-` (HarmonyOS
project), `AGC-` (AppGallery rules), `HMS-` (Android APK on AppGallery). What
each ID means, how to verify it and the standard fix are in
`references/apple.md`, `references/google.md` and `references/huawei.md`
(search for the ID). Read only the files for the platforms the app ships to.

## 3. Verify every finding

For each finding, read the evidence files (in parallel) and decide:

- **Confirmed**: the code shows the violation. Keep it, cite `file:line`.
- **Downgraded**: real but mitigated (behind `kDebugMode`/`__DEV__`, a dead
  code path, handled in a backend you cannot see). Lower the level and say why.
- **Dropped**: false positive (a comment, a test fixture, an unrelated word).
  Do not report it. Mention the count of dropped leads in one line.

Evidentiary standard:

1. Presume compliance. CRITICAL and IMPORTANT need a cited line that shows the
   problem. Suspicion alone is at most a SUGGESTION.
2. Do not guess what happens behind an interface or a backend call. If the
   answer lives in a backend or a console, file it under **Manual checks**.
3. Local-only data (theme, on-device cache) is not "collection" for privacy
   forms and needs no deletion flow.
4. When verifying a lead, bound your reads to the evidence files and their
   direct callers.

Then look for what the scanner cannot see, with **targeted** searches (grep for
a specific API or key, then read the hits):

- Remote Config templates and defaults (`remoteconfig*.json`,
  `remote_config_defaults.*`): flags that default to off and switch on a
  feature later are 2.5.19 material.
- Every call site of the microphone, camera, location and contacts APIs: is the
  use started by the user, disclosed, and covered by the purpose string? A
  purpose string that is specific but leaves out a real use (the microphone
  string names editing but not song recognition) is a 5.1.1(ii) finding.
- Every user-content surface (feeds, comments, chat, shared outputs): report and
  block on each one, not only on one of them.
- What each SDK in `facts.sdk_categories` sends where (for the privacy forms).
- Admin, operator or staff screens gated by a role: harmless, but document
  them in the review notes.
- The "Beyond the scanner" list at the end of each reference file.

## 4. Write the report

Write in the user's language (`--lang` overrides). Rule names and guideline
numbers stay as the stores write them. Use `references/report-template.md`.

- One file per app: `store-compliance-<app>-<YYYY-MM-DD>.md`. Save it to the
  directory the user named, otherwise to `~/store-compliance-reports/`. Print
  the path.
- In chat give the summary table (counts per level) and the top 3 risks,
  unless the caller asked for more (for example a per-finding verdict list).
  The details belong in the file.
- Order: CRITICAL, then IMPORTANT, then SUGGESTION, then Manual checks.
- Platform column: **Apple**, **Google** or **Huawei** when only that store's
  rules are broken. Name every store when each has its own rule against it
  (account deletion, third-party AI consent, UGC moderation), for example
  **Apple · Google · Huawei**. `both` findings name only the stores the app
  ships to.
- HarmonyOS apps ship only in mainland China, so the Chinese AppGallery rules
  (V52), ICP filing and the personal information rules always apply to them.
- A downgraded finding keeps a one-line "Downgraded from X because …" note.
- Every finding: **what** (one sentence), **evidence** (`file:line`),
  **rule** (guideline/policy + date if new), **risk** (what the store does:
  rejection, removal, update block, account action), **fix** (concrete code or
  console change, with a snippet when it is short).
- Deadlines that are already past are written as "in force since …", not as
  upcoming.

## 5. Many repos

Scan each repo, then write one `store-compliance-summary-<date>.md` with a row
per app (CRITICAL / IMPORTANT / SUGGESTION counts and the top issue). If your
agent can run subagents, run steps 2–4 per repo in subagents, at most 3 at a
time, and pass them this file's path so they follow the same rules. Otherwise
go through the repos one by one.

## 6. After the report

Do not change the audited code unless the user asks. When asked to fix:
one logical change per commit, following the repo's own conventions, and
re-run the scanner afterwards to show the finding is gone.

## Notes

- Native Android projects can also be checked with Google's
  `play-policy-insights` skill (github.com/android/skills, `play/`), which goes
  deeper into Data safety for Java/Kotlin. This skill covers all three stores
  and cross-platform stacks.
- The scanner cannot see App Store Connect, Play Console or AppGallery Connect.
  Store listing text, screenshots, age-rating answers, Data safety and App
  Privacy forms, the AppGallery privacy statement and ICP filing are always in
  **Manual checks**.
- Taro keeps its HarmonyOS project outside the repo, and uni-app may not commit
  `harmony-configs/entry`. If `facts.platforms` lacks `harmonyos` for such an
  app, say the HarmonyOS manifest was not scanned.
