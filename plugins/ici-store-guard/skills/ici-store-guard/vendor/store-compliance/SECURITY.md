# Security policy

## Supported versions

Only the latest release on `main` receives fixes.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's
[private vulnerability reporting](https://github.com/motivexintelligence/store-compliance-skill/security/advisories/new)
or email **info@motivexintelligence.com** with:

- what the problem is and where (file and line),
- how to reproduce it,
- what an attacker could do with it.

We aim to reply within 5 working days and to publish a fix and an advisory once it is
resolved. Credit is given unless you prefer otherwise.

## Scope

The scanner reads untrusted repositories, so the following are in scope:

- a crafted repository that makes `scripts/scan.py` write files, run commands, reach the
  network or read outside the scanned folder,
- a crafted file that makes the scanner hang or exhaust memory,
- instructions in `SKILL.md` or the references that could lead an agent to leak data or run
  unsafe commands.

Wrong or outdated store rules are not security issues. Please open a normal issue for those.
