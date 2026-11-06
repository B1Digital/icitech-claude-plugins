# Report template

Write the report in the user's language. Keep headings short. Translate the
headings below, keep IDs, guideline numbers and policy names as the stores
write them.

```markdown
# Store compliance: <App name> (<version>)

<repo path> · <git HEAD short sha and date> · scanned <YYYY-MM-DD> · rules as of <rules-as-of>
Platforms: iOS, Android, HarmonyOS · Stack: <Flutter 3.x / Expo SDK nn / native / ArkTS>

## Summary

| Level | Apple | Google | Huawei | Several stores |
|---|---|---|---|---|
| 🔴 Critical | n | n | n | n |
| 🟡 Important | n | n | n | n |
| 🔵 Suggestion | n | n | n | n |
| ☑️ Manual check | n | n | n | n |

Drop the Huawei column when the app does not ship to AppGallery.

**Top risks**
1. <one line: what, which store, what happens>
2. …
3. …

## 🔴 Critical

### 1. <short title> · <Apple 2.5.19 / Play Billing Library 8 / AppGallery 3.16>
- **What:** one sentence.
- **Evidence:** `lib/foo/bar.dart:42`, `ios/Runner/Info.plist:31`
- **Rule:** guideline or policy, with the date when it is a 2026 change.
- **Risk:** rejection / removal from the store / updates blocked / developer account action.
- **Fix:**
  <concrete steps, short code or config snippet>
- _Downgraded from CRITICAL: <reason>._ (only when you lowered the scanner's level)

## 🟡 Important
…

## 🔵 Suggestions
…

## ☑️ Manual checks (App Store Connect / Play Console / AppGallery Connect)
- [ ] <item> (why it applies to this app)

## Rule changes since the references
<only if step 0 found newer rules, otherwise omit the section>

<sub>Dropped <n> scanner leads as false positives after reading the code.</sub>
```

Style:
- One finding per real problem. Merge several files with the same cause.
- Say what the store does, plainly. No "might potentially".
- Fixes name the exact file, key or package version.
- Past deadlines: "in force since 31 Aug 2026". Future ones: "from 27 Jan 2027".
