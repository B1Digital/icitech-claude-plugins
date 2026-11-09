# Vendored sources

Read and reviewed before vendoring on 2026-11-06. Scripts are stdlib-only Python.
Network access: only `play-policy-insights/scripts/play_store_scraper.py` (reads the
public Google Play listing + Data safety page for the package name). Nothing else
calls out.

| Folder | Upstream | Commit | License |
|---|---|---|---|
| `appstore-review-skill/` | github.com/devsemih/appstore-review-skill | ab77bb7 | MIT |
| `store-compliance/` | github.com/motivexintelligence/store-compliance-skill (assets/tests dropped) | 6ca27a8 | MIT |
| `play-policy-insights/` | github.com/android/skills — `play/play-policy-insights` | bf68e2d | Apache-2.0 |

## Evaluated and NOT vendored (bake-off on a Flutter + Flame game, 2026-11-06)

| Candidate | Result |
|---|---|
| danieleborghe/apple-appstore-compliance-checker | No new findings; scanners Dart-only, CRITICAL false positive on Flame `camera`, writes JSON into the audited repo |
| chingiz/appstore-preflight | Method valuable (binary checks) but scripts are Swift/Xcode-archive oriented — distilled into `references/binary-and-assets.md` instead |
| eudresfs/mobile-hig-audit | Scanner blind to Dart (4/4 findings false); its screenshot/metadata checklist idea kept in `binary-and-assets.md` |
| MaTriXy/StoreReady | Go binary, not built (unreviewed external code); targets Kotlin/Swift/RN, not Flutter |
| Hritik602/mobile-store-review-skills | Not vendored; its cross-platform ideas (declaration drift, behavioural drift, deep-link parity, parity matrix) are written into SKILL.md Phase 3 |
| anagnole/apple-reviewer-simulator | Replaced by our own runtime walkthrough |
| Maestro (mobile-dev-inc/Maestro), Dart & Flutter MCP (dart-lang/ai) | Not vendored — external tools the skill uses when installed (Phase 4) |
| mobile-next/mobile-mcp, Appium | Same job as Maestro; one driver is enough |
| Patrol, flutter/agent-plugins, dart-lang/skills, android testing-setup, flutter-ai-rules | Test-writing / code-quality, not pre-submission review |
| android/skills android-permissions-security | Binder/IPC security; Play restricted-permission policy already covered by play-policy-insights |
| Semgrep, SonarQube, Sentry, Superpowers | Security / quality / production monitoring / generic workflow — out of scope |

## Updating

```bash
T=$(mktemp -d)
git clone --depth 1 https://github.com/devsemih/appstore-review-skill $T/a
git clone --depth 1 https://github.com/motivexintelligence/store-compliance-skill $T/b
git clone --depth 1 --filter=blob:none --sparse https://github.com/android/skills $T/c && git -C $T/c sparse-checkout set play/play-policy-insights
```

Diff each against the folder here, read any changed script before copying it in,
then update the commit column above.
