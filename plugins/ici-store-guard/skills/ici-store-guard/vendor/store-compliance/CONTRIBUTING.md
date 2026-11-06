# Contributing

Thanks for helping keep store-compliance accurate. Store rules change often, so the most
useful contributions are rule updates with a source, new checks with a test, and reports
of false positives.

## Ground rules

- **Every rule needs a source.** Link the official page (Apple Developer, Play Console Help,
  Huawei developer docs) and give the date it was published or last updated. Secondary
  sources are fine as a pointer, but mark anything you could not confirm on an official page
  as unverified.
- **The scanner stays small and safe.** Python standard library only, read-only, no network
  access, no writes into the scanned repo. It must keep running on Python 3.9.
- **Leads, not verdicts.** The scanner finds candidates. The agent confirms them by reading
  the code. Prefer a check that misses a rare case over one that floods reports with false
  positives.
- **Keep the skill agent-neutral.** `SKILL.md` follows the [Agent Skills](https://agentskills.io)
  standard. Do not add instructions that only one agent understands without a fallback.

## Updating a rule

1. Edit the matching file in `references/` (`apple.md`, `google.md` or `huawei.md`).
2. Bump `rules-as-of` at the top of that file and `metadata.rules-as-of` in `SKILL.md`.
3. If a deadline moved from "upcoming" to "in force", say so in the table.
4. Add a line to `CHANGELOG.md`.

## Adding a scanner check

1. Pick an ID with the right prefix: `X-` (more than one store), `IOS-`, `AND-`, `EXPO-`,
   `HOS-` (HarmonyOS project), `AGC-` (AppGallery rule), `HMS-` (Android on AppGallery).
2. Add the check in `scripts/scan.py` with a level (`CRITICAL`, `IMPORTANT`, `SUGGESTION`),
   the rule it cites in `refs`, a one-sentence title and `file:line` evidence.
3. Document the ID in the reference file: rule, how to verify, fix.
4. Make a fixture in `tests/fixtures/` trigger it and add the ID to the expected set in
   `tests/test_scan.py`.
5. Run the scanner on a few real apps and check it stays quiet where it should.

## Reporting a false positive

Open an issue with the finding ID, the evidence line the scanner printed, and why it is
not a violation. A small code snippet is enough. Never paste secrets or private code.

## Running the tests

```bash
python3 -m unittest discover -s tests
```

## Pull requests

- One logical change per pull request.
- Tests pass, and the reference and the changelog are updated with the code.
- Write plainly. Short sentences, no marketing language.
