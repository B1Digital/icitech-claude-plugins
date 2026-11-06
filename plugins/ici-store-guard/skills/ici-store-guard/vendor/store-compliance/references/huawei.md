# Huawei AppGallery and HarmonyOS: what to check in code

Rules as of **2026-11-05**. Covers two kinds of app:

- **HarmonyOS apps** (HarmonyOS 5+, ArkTS, Stage model, `.hap` / `.app`), native or
  through Flutter for OpenHarmony (`ohos/`), React Native for OpenHarmony (`harmony/`),
  uni-app (`harmony-configs/`) or Taro.
- **Android APK/AAB on AppGallery**, which run on Huawei devices without Google
  Mobile Services (HMS Core instead).

## Which rulebook applies

| Rulebook | Version | Applies to |
|---|---|---|
| **应用审核指南** (Chinese) | **V52, 2026-10-29** | China AppGallery: every HarmonyOS app and any APK distributed in mainland China |
| AppGallery Review Guidelines (English) | sections updated 2023–2026 | Global AppGallery, in practice Android APKs outside mainland China |
| 应用审核 Checklist | 2026-10-29 | Pre-submission self-check |

HarmonyOS phone, tablet and PC apps are **distributed only in mainland China**
(watches excepted). So for a HarmonyOS app the Chinese V52 rules, **ICP filing
(APP备案)**, the software copyright certificate and the PIPL/MIIT personal
information rules always apply. The Chinese text is stricter than the English
one: the HUAWEI ID rule, the 15-working-day deletion deadline and the
"two lists" (双清单) exist only in Chinese.

Huawei's own list of the most common rejections: no ICP filing, missing
qualification documents, personal information violations (Section 7), broken
features, UX issues (dark mode, contrast), copycat apps, and test data or
test builds. Single-function and duplicate apps follow closely.

## Deadlines and recent changes

| Date | Change | Status on 2026-11-05 |
|---|---|---|
| 2025-09-01 | China's AI-generated content labelling rules. AppGallery Connect asks for an **AI feature declaration** at submission and checks the labels | In force |
| 2025-11-10 | Package validity check includes HarmonyOS ecosystem rule checks | Live |
| 2025-11-25 | HarmonyOS phone and tablet apps are released to PC/2in1 by default | Live. Apps must work there |
| 2026-08-29 | HarmonyOS SDK 26.0.0. API levels switch to `"26.0.0"` | Released |
| 2026-09-07 | Huawei asks developers to raise `targetSdkVersion` to API 26 | Recommendation. Package warning **7031** |
| 2026-10-29 | Review guidelines V52 | Current |
| **2027-01-01** | AppGallery Connect shows upgrade prompts for old target SDKs on upload | Advisory, no hard block announced |

---

## Findings by scanner ID

`HOS-*` = HarmonyOS project, `AGC-*` = AppGallery rules for both kinds,
`HMS-*` = Android APK on AppGallery.

### HOS-PERM-DECLARE: `reason` and `usedScene` (permission declaration)
- **Rule.** Every permission is declared in `module.json5` → `module.requestPermissions[]`. For `user_grant` and `manual_settings` permissions `reason` and `usedScene` are mandatory. A reason that does not match the real use gets the permission and the app rejected.
- **Reason text.** A `$string:` resource, not empty, at most 256 characters (under 72 recommended), in the form "Used for video calls." Vague text ("使用相机", "需要权限", "needs permission") is a counter-example. Provide every locale the app ships. HarmonyOS shows this text inside the system permission dialog.
- **Fix.** `{ "name": "ohos.permission.CAMERA", "reason": "$string:camera_reason", "usedScene": { "abilities": ["EntryAbility"], "when": "inuse" } }` and a concrete sentence per locale.

### HOS-PERM-RESTRICTED: restricted permissions (ACL)
- **Rule.** About 90 permissions are `system_basic` and only reachable through ACL for narrow use cases. Huawei: use the Picker or security control first. Otherwise the app is rejected. A restricted permission must be requested in the **release Profile** and justified with a usage video at submission. Package permissions that are not in the Profile fail with error **7014**.

| Permission | Allowed only for | Use instead |
|---|---|---|
| `READ_IMAGEVIDEO` | backup/clone/sync, gallery organisers, auto video generation | `photoAccessHelper.PhotoViewPicker` |
| `WRITE_IMAGEVIDEO`, `SHORT_TERM_WRITE_IMAGEVIDEO` | | **SaveButton** security control |
| `READ_AUDIO`, `WRITE_AUDIO` | backup/clone/sync | `AudioViewPicker` |
| `READ_CONTACTS`, `WRITE_CONTACTS` | backup/clone/sync | Contact Picker (`contact.selectContacts`), or open the Contacts app |
| `READ_PASTEBOARD` | PC/2in1, a few phone cases (bank card paste, share codes, editors, IMEs) | **PasteButton** security control |
| `READ_WHOLE_CALENDAR`, `WRITE_WHOLE_CALENDAR` | | `READ_CALENDAR` / `WRITE_CALENDAR` |
| `SYSTEM_FLOAT_WINDOW` | PC/2in1 calls and screen sharing | Picture-in-picture |
| `GET_WIFI_LOCAL_MAC` and other MAC/IP identifiers | | OAID or app-scoped IDs |
| `KEEP_BACKGROUND_RUNNING_SYSTEM`, `…_SPECIAL_SCENARIO` | | Normal continuous tasks |

Security controls fail silently when they are too small, transparent, low-contrast or covered (log keyword `SecurityComponentCheckFail`). Full list: developer.huawei.com/consumer/cn/doc/harmonyos-guides/restricted-permissions.

### HOS-PERM-DEPRECATED
`ohos.permission.READ_MEDIA` and `WRITE_MEDIA` are deprecated since API 22. Older Flutter-OHOS and RNOH templates still declare them. Use the Pickers.

### HOS-PERM-LOCATION
- **Rule.** `ohos.permission.LOCATION` (precise) only together with `ohos.permission.APPROXIMATELY_LOCATION`. `LOCATION_IN_BACKGROUND` cannot be granted by the dialog: the user turns it on in Settings, and Huawei prefers a location continuous task. Location may not be requested only for ads or analytics (7.17), and location tracks may not be used for marketing (7.16).
- **Fix.** Declare both foreground permissions, prefer approximate, use a continuous task instead of background location.

### HOS-PERM-STARTUP: permissions asked at launch (7.17–7.19)
- **Rule.** Ask for each permission when the user starts the feature. No dialogs on first launch before the feature is used, no bundling, no loops, no exit or blocked login after a denial. After a denial, ask again only when the user triggers the feature again (Chinese testing practice: not more than once in 48 hours, from GB/T 41391-2022).
- **Verify.** `requestPermissionsFromUser(` in `EntryAbility` (`onCreate`, `onWindowStageCreate`) or the first page's `aboutToAppear`. `terminateSelf()` in a denial branch.
- **Fix.** Move the request behind the feature's button. On denial, degrade and offer `requestPermissionOnSetting()` from an explicit tap.

### HOS-CONSENT-FIRST: privacy consent before any collection (7.1, 7.5)
- **Rule.** A privacy policy dialog on first launch (or a clear notice on the sign-up/login screen) must get consent **before** the app or any SDK collects personal data or asks for permissions. It needs separate **agree and decline** buttons. Not acceptable as the consent button: "好的", "我知道了", "我已阅读", "立即使用", "下一步". No pre-ticked boxes, no "logging in means you agree" without a checkbox. Simplified Chinese version, developer and app name exactly as in AppGallery Connect, sensitive processing highlighted, the same URL in the app and the console.
- **Verify.** SDK init in `EntryAbility.ets` or `AbilityStage` (analytics, push token, OAID, crash reporting, `AGConnect`, Umeng, Bugly) with no consent flag check before it.
- **Fix.** Gate every SDK init and permission request on a stored consent flag. Two buttons: 同意 / 不同意. Link the policy from the dialog, the login screen and settings.

### HOS-BUILD-GATES: upload checks
| Check | Where | Result |
|---|---|---|
| `bundleName` matches the AppGallery app, same across HAPs, ≥ 3 segments, 7–128 bytes | `AppScope/app.json5` | Errors 992 / 997 |
| `versionCode` increases every release | `AppScope/app.json5` | Rejected |
| `bundleType` is `app` (or absent) for apps | `AppScope/app.json5` | Rejected |
| No debug build (`"debug": true`) | `app.json5`, `module.json5` | Rejected, also 3.8 |
| `compatibleSdkVersion` API ≥ 10 | `build-profile.json5` → `app.products[]` | Error 1021 |
| `targetSdkVersion` API 26 recommended | `build-profile.json5` | Warning 7031, prompts from 2027-01-01 |
| Release certificate and release Profile (not DevEco auto-signing) | `build-profile.json5` → `signingConfigs` | Errors 993, 999, 1000–1002, 7017 |
| `deviceTypes` match the devices selected in AppGallery Connect, never `default` and `phone` together | `module.json5` | Errors 998, 12 |

SDK versions are written `"5.0.0(12)"` (API 12) up to API 25 and `"26.0.0"` from API 26. `runtimeOS: "OpenHarmony"` projects cannot use HarmonyOS kits (Account, IAP, Push). Committed `.p12` / `.p7b` / `.cer` files are signing secrets and do not belong in the repo.

### HOS-HUAWEI-ID: HUAWEI ID login (3.16)
- **Rule.** "若应用支持用户使用第三方账号登录，则该应用需提供华为账号登录选项。" A HarmonyOS app that offers third-party login (WeChat, QQ, Weibo, Alipay, Apple, Google) must also offer HUAWEI ID login. Phone or email login alone does not trigger it. Atomic services with an account system must use HUAWEI ID. Account Kit also needs a `client_id` entry in `module.json5` → `module.metadata`.
- **Fix.** `LoginWithHuaweiIDButton` from `@kit.AccountKit` next to the other social logins, and the `client_id` metadata.

### HOS-OHPM-DEPS
Wildcard (`"*"`, `"latest"`) dependencies in `oh-package.json5` make the shipped SDK set unpredictable, which breaks the SDK disclosure list (7.2). Hot-update or code-push libraries break 3.13 (see X-CODE-PUSH).

### AGC-ICP-FILING: APP备案
- **Rule.** Apps that provide internet information services in mainland China must be filed with MIIT **through their hosting provider** (Huawei Cloud, Alibaba Cloud, Tencent Cloud…). Missing filing is the #1 rejection, and Huawei devices warn "应用未核准（备案）" on install. For HarmonyOS, the filing must tick the **鸿蒙 platform** and list **every bundleName**. An app already filed for Android or iOS needs a change filing. The app name, package name and entity must equal the listing. Mainland listings also need an electronic **software copyright certificate** (软著) whose name matches the app.
- **In AppGallery Connect.** "核准（备案）信息": server in mainland China (filed), server outside mainland China (foreign entity and foreign servers only), or offline app.
- **Verify.** Not provable from code. Report it when the app targets HarmonyOS, or has a China/Huawei Android flavor, and talks to a server.

### AGC-PRIVACY-LISTS: SDK list, two lists and personalisation switch (7.2, 7.4, 7.7)
- **SDK list.** Every SDK that processes personal data is listed one by one in the privacy policy (name, developer, data, purpose, SDK policy link), matching the national SDK registry (全国SDK管理服务平台). No data to SDKs before consent.
- **Two lists (双清单).** An in-app **collected personal information list** (已收集个人信息清单) and a **third-party sharing list** (第三方共享个人信息清单), usually Settings → Privacy (MIIT 2021-292).
- **Personalisation.** When personal data drives recommendations, ads or marketing, the app has an **independent off switch** that really stops it, and personalised content is labelled (个性化推荐).
- **Fix.** Add the two list pages and the switch, and pass the switch to the recommendation API and ad SDKs.

### X-ACCOUNT-DELETION: account deletion (7.3)
Account deletion (注销账号) must really delete the data and complete within **15 working days**, also for apps that only use third-party login. Warn about active auto-renewing subscriptions before deletion.

### AGC-OAID: advertising identifier (7.21–7.25)
- **Rule.** OAID only for ads and analytics, never joined with IMEI, MAC, serial numbers or identity without explicit consent. Check the limit-tracking state **every time** before use. Do not link a reset OAID to the old one.
- **HarmonyOS.** `identifier.getOAID()` from `@kit.AdsKit` needs `ohos.permission.APP_TRACKING_CONSENT` (with `reason`). Without it the OAID is all zeros.
- **Android.** `com.huawei.hms:ads-identifier`, `AdvertisingIdClient.getAdvertisingIdInfo(` with `isLimitAdTrackingEnabled()`.

### AGC-ADS: ads (Section 5)
- **Rule.** Ads are labelled 广告, closable with one visible, real tap (no delayed or countdown-only close), never on system keys, outside the app, after exit or on the lock screen. **No ads in widgets or extensions** (5.9). At most two ad elements per screen (5.7). No promotion of other app stores (5.6). Shake-to-open splash ads must explain the action and not use high sensitivity (MIIT 2023-26). Children's apps: no ads outside parent-gated areas.
- **Verify.** `@kit.AdsKit` or `advertising.` inside `*FormAbility*.ets` / `form_config.json` modules. Android: `com.huawei.hms:ads-lite`, Pangle CN, GDT (`com.qq.e`), Kuaishou (`com.kwad.sdk`), Baidu.

### X-IAP-RESTORE, X-PAYWALL-TERMS, X-LOOT-BOX: payments (Section 6)
- **IAP.** HUAWEI IAP / IAP Kit is **recommended, not required** (6.4). No rule bans WeChat Pay or Alipay. Games must redeliver consumables lost to network errors (6.6).
- **Auto-renewal (6.2).** Price and renewal shown before purchase, a **single-purchase option next to auto-renew** (cloud storage exempt), nothing pre-ticked, explicit consent before a trial converts, a **reminder 5 days before each charge**, an in-app subscription management page, cancellation without extra identity checks.
- **Paywalls (6.3).** Membership benefits and fees clear. Loot boxes and blind boxes show rules and **probabilities** before purchase. Paid pop-ups have a one-tap close.

### X-AI-DATA-SHARING, X-AI-IMAGERY: AI declaration (2025-09-01)
Declare AI generation features at submission, label generated content visibly ("AI生成") and in file metadata, and upload the labelling material and any generative AI filing (深度合成 / 生成式AI备案).

### X-UGC-MODERATION, X-UGC-PRESENT: user content (4.14, 4.15)
Verify account identity, filter names, bios, posts and comments, ban serious violators, publish contact info. The report entry must say **举报** or **投诉**. "问题反馈" (feedback) does not count.

### X-CODE-PUSH: no self-update (3.13)
"应用不得绕过审核机制进行自动更新". No downloading of code that changes features, no APK self-install (`REQUEST_INSTALL_PACKAGES` installer flows), no Tinker, Sophix or Robust hotfixes, no `.hap`/`.hsp` downloads. Use AppGallery's update component or a store link.

### X-KIDS-AUDIENCE: minors (1.10, Section 8)
Age rating levels 3+, 8+, 12+, 16+, 18+. Children's apps need a children's privacy policy, guardian consent, and parent-gated purchases and links. Games, live streaming, video and social apps offer time, permission and spending controls for minors (8.3). Games show the copyright holder, publisher, approval number, ISBN and the 健康游戏忠告 on launch for at least 2 seconds (3.17). Stranger chat, live shows and dating may not target minors.

### X-PLACEHOLDER, X-WEBVIEW-WRAPPER: function quality (Section 3)
No test builds or test data (3.4), no single-page, web-wrapper or template apps (3.5), no duplicates (3.6). Saturated categories (calculator, flashlight, notes, bookkeeping, weather, compass, random picker, wooden fish) need a clear difference (3.7). Must work on **IPv6** (3.14): no hard-coded IPv4 API addresses. No emoji, "免费", "官方", "test" or "beta" in the app name (1.4–1.5).

---

## Android APK/AAB on AppGallery

### HMS-GMS-DEPENDENCY: depends on Google Mobile Services
- **Rule.** The app must install, start and work on mainstream Huawei devices (3.1). Huawei phones since 2019 ship without GMS. A core flow that needs GMS (FCM push, Google Sign-In as the only login, Play Billing as the only payment, Google Maps, SafetyNet or Play Integrity gates, Play Core update or review) breaks on the review device. Listings must not show other stores' badges (1.16).
- **Verify.** GMS dependencies with no HMS counterpart and no `GoogleApiAvailability` / `HuaweiApiAvailability` fallback, in an app that ships to AppGallery (`agconnect-services.json`, `com.huawei.*` dependencies or a `huawei` flavor).
- **Fix.** A `huawei` flavor with HMS Push (`com.huawei.hms:push`), HUAWEI ID (`com.huawei.hms:hwid`) or email login, HMS IAP, Petal Maps, Location Kit, Safety Detect, and a graceful fallback when GMS is missing. The separate package name also needs Android developer verification (see google.md AND-SIDELOAD-FLAVOR).

### HMS-AGC-CONFIG: HMS integration files
- **Verify.** `com.huawei.hms:*` or `huawei_*` plugins without `agconnect-services.json` in the app module, without the `com.huawei.agconnect` Gradle plugin, or without the `https://developer.huawei.com/repo/` Maven repository. HMS dependencies applied to the Google Play flavor too (keep them in a `huawei` flavor). HMS init (push token, analytics, OAID) before privacy consent.
- **Fix.** Add the config file and plugin, keep HMS in its own flavor, gate init on consent. Register the signing SHA-256 fingerprint in AppGallery Connect for Account, IAP and Push.

### Chinese privacy rules apply to APKs too
Everything under HOS-CONSENT-FIRST, AGC-PRIVACY-LISTS, AGC-OAID and X-ACCOUNT-DELETION applies to APKs distributed in mainland China. MIIT testers look for `getImei`, `getDeviceId`, `ANDROID_ID`, MAC address and installed-package reads in `Application.onCreate` or SDK init before consent, and for self-start or chain-start of other apps (7.9).

### Global AppGallery
English rules: privacy policy in the app and the console (7.1), consent before collection where consent is the legal basis (7.5), personalised-ads opt-out (7.7), OAID rules, HUAWEI IAP recommended, no self-update (3.9), IPv6 (3.10), age assurance for adult apps where laws require it (8.14). No ICP filing, no software copyright certificate, no HUAWEI ID rule. No current targetSdk floor is published. A Play-compliant targetSdk passes.

---

## Where the HarmonyOS config lives

| Framework | `module.json5` | `app.json5` | `build-profile.json5` | Dependencies |
|---|---|---|---|---|
| Native ArkTS | `entry/src/main/module.json5` (+ feature modules) | `AppScope/app.json5` | `build-profile.json5` | `oh-package.json5` |
| Flutter for OpenHarmony | `ohos/entry/src/main/module.json5` | `ohos/AppScope/app.json5` | `ohos/build-profile.json5` | `ohos/oh-package.json5`, `*_ohos` plugins |
| React Native for OpenHarmony | `harmony/entry/src/main/module.json5` | `harmony/AppScope/app.json5` | `harmony/build-profile.json5` | `harmony/oh-package.json5` |
| uni-app | `harmony-configs/entry/src/main/module.json5` | `harmony-configs/AppScope/app.json5` (manifest.json wins) | `harmony-configs/build-profile.json5` | `harmony-configs/oh-package.json5` |
| Taro | in the DevEco project at `config` → `harmony.projectPath`, often outside the repo | same | same | same |

If the HarmonyOS project is outside the repo (Taro) or `harmony-configs/` has no `module.json5`, say so and ask for it.

---

## Beyond the scanner (always list under Manual checks if relevant)

- **APP备案** with the 鸿蒙 platform and every bundleName. Software copyright certificate for mainland listings.
- **Privacy statement in AppGallery Connect** matches the in-app policy, lists every SDK, and the permission reasons match `module.json5`.
- **Restricted permissions** requested in the release Profile, with a usage video for each.
- **AI feature declaration** and labelling material.
- **Age rating** (3+, 8+, 12+, 16+, 18+) and children's category answers.
- **Test account** that works, and a demo video for hardware features (1.21).
- **PC/2in1**: phone apps are released there by default, check the layout.
- **Dark mode and contrast** (UX standard, a top-5 rejection reason).
- **Data export statement** when a non-mainland region is selected.

Unverified at the time of writing: the status of the location security control
(LocationButton), the exact 48-hour clause, shake-ad sensitivity numbers, any
AppGallery targetSdk floor for APKs, minimum HMS Core SDK versions, and whether
AppGallery accepts `runtimeOS: "OpenHarmony"` packages.

## Sources

- 应用审核指南 V52: https://developer.huawei.com/consumer/cn/doc/app/50104 · English: https://developer.huawei.com/consumer/en/doc/app/50104
- Review checklist: https://developer.huawei.com/consumer/cn/doc/doccenter-submission/50170
- APP备案: https://developer.huawei.com/consumer/cn/doc/app/50130
- Permissions: https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/declare-permissions · restricted: https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/restricted-permissions
- Package error codes: https://developer.huawei.com/consumer/cn/doc/doccenter-operations/agc-help-package-errorcode-0000002312513009
- API 26 notice: https://developer.huawei.com/consumer/cn/notice/detail/?id=9002210958618976001
- Account Kit rules: https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/account-detailedrules
- MIIT 2021-292 (two lists) and 2023-26 (ads, permissions): miit.gov.cn
