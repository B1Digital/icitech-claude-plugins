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
| Hritik602/mobile-store-review-skills, anagnole/apple-reviewer-simulator | Overlap with vendored skills / our own runtime walkthrough |

## Updating

```bash
T=$(mktemp -d)
git clone --depth 1 https://github.com/devsemih/appstore-review-skill $T/a
git clone --depth 1 https://github.com/motivexintelligence/store-compliance-skill $T/b
git clone --depth 1 --filter=blob:none --sparse https://github.com/android/skills $T/c && git -C $T/c sparse-checkout set play/play-policy-insights
```

Diff each against the folder here, read any changed script before copying it in,
then update the commit column above.
