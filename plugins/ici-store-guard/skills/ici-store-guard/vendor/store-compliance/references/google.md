# Google Play Developer Policies: what to check in code

Rules as of **2026-11-05**. Sources: Play Console Help policy announcements
(29 October 2026, 15 July 2026, 15 April 2026), the Policy deadlines table
(support.google.com/googleplay/android-developer/table/12921780), the
technical quality requirements (answer/17492799), the Play Policy Center and
developer.android.com/blog (the Android Developers Blog moved there on
2026-10-15).

## In force

| Since | Policy | Notes |
|---|---|---|
| 2026-08-31 | **Target API level 36** (Android 16) for new apps and updates on phones and tablets. **Wear OS and Android Automotive: 35. Android TV and Android XR: 34** | The last extension ended 2026-11-01. No extensions left |
| 2026-08-31 | **Play Billing Library 8+** for new apps and updates | Extensions ended 2026-11-01 |
| 2026-08-26 | Anonymous and random chat apps fall under Child Endangerment and Age-Restricted Content rules and may not target children | |
| 2026-07-15 (+30 days) | User Data policy covers **third-party AI**: limited use, disclosure, consent. Unrated apps not allowed | |
| 2026-04-15 | Account Transfer: only the official transfer tool, no account marketplaces | Console |
| 2025-10-30 (+30 days) | **Age-Restricted Content and Functionality**: dating and real-money gambling apps must block minors with the Play Console tools | |
| 2026-09-30 | Android developer verification. Play auto-registered about 99% of apps. Unregistered apps and package names that ship **only outside Play** must be registered. Sideload enforcement is live in Brazil, Indonesia, Singapore and Thailand, global in 2027 | Console |

## Upcoming

| Date | Policy | Who is affected |
|---|---|---|
| Nov 2026 → **2027-01-27** | **Precise location declaration**: every app requesting `ACCESS_FINE_LOCATION` explains in Play Console why coarse location or the location button is not enough. For **targetSdk 37+** the location button is **mandatory** for one-time precise location (the deadlines table still says "recommended") | 30-day self-extension in Console |
| 2026-12-01 | Japan payment authorization | Accounts selling to or from Japan, Console only |
| 2027-01-27 | **Contacts**: targetSdk 37+ apps without a core need use the Contact Picker. `READ_CONTACTS` declaration | |
| 2027-01-27 | **READ_CALL_LOG** no longer allowed for phone-call verification. Use the Digital Credentials API, the SMS Retriever API or the SMS User Consent API | |
| 2027-01-27 | **Foreground services**: geofencing removed as an approved use. Use the Geofence API | |
| 2027-01-27 | **Eligibility-based subscription discounts** (student, teacher, military, senior) must state the criteria, how eligibility is checked and the price after eligibility ends | |
| 2027-02-01 | **16 KB page size**: updates without 16 KB support cannot be released | targetSdk 35+ with native code |
| 2027-02-01 | **Trader status** declared for every account. Missing it blocks updates and removes apps globally. Traders give a Terms of Service URL per app | Console |
| 2027-02-01 | US external content links: download reporting and fees | Enrolled US developers |
| Feb 2027 | **Memory thresholds** and **DEX optimization ≥ 25%** (obfuscation, optimization, shrinking) when DEX > 10 MB (games > 50 MB) | Reduced visibility, then publishing limits |
| Apr 2027 | **Zero-tap sign-in**: apps with sign-in must restore the signed-in state on a new device (Restore Credentials API). Games exempt for now | Reduced visibility |
| 2027-04-14 | **AppFunctions**: functions exposed to AI agents must not deceive agents, bypass security or drive other apps | `androidx.appfunctions` |
| 2027-08-25 | **Local network** (`ACCESS_LOCAL_NETWORK`) declaration for targetSdk 37+ | Prompts from June 2027 |
| 2027-08-25 | **Manage contacts** (`MANAGE_CONTACTS`) restricted. Direct `WRITE_CONTACTS` writes stop at targetSdk 38 | Prompts from summer 2027 |
| 2027-08-31 | **Play Billing Library 9+** for new apps and updates (extension to 2027-11-01) | |
| 2027 | Android developer verification global on certified devices | Apps distributed outside Play |

Still in force from earlier rounds and frequently hit: account deletion (in-app
and web link), Data safety accuracy, Photo and Video Permissions (Photo
Picker), exact alarm, foreground service types, AI-Generated Content (in-app
reporting), Child Safety Standards (published CSAE standards for social apps),
Families ads, organization accounts for regulated categories.

---

## Findings by scanner ID

### AND-TARGET-SDK, AND-TARGET-SDK-UNKNOWN: Target API level
- **Rule.** New apps and updates target API 36 on phones and tablets, 35 on Wear OS and Automotive, 34 on TV and XR. Existing apps below the floor are hidden from new users on newer devices.
- **Verify.** `facts.android_sdk_levels.targetSdk`. For Flutter, `flutter.targetSdkVersion` is resolved from the pinned SDK (`.fvmrc`) or the global one. Form factor comes from `<uses-feature>` (`android.hardware.type.watch`, `android.software.leanback`, `android.hardware.type.automotive`).
- **Fix.** `targetSdk = 36`, then test the Android 16 behaviour changes (see AND-EDGE-TO-EDGE, AND-PREDICTIVE-BACK, AND-ORIENTATION-LOCK).

### AND-BILLING-VERSION, AND-BILLING-PBL9: Play Billing Library deprecation
- **Rule.** PBL 8+ since 2026-08-31, no extensions left. Older versions block every update (security fixes included). PBL 8 itself is deprecated on **2027-08-31**: new apps and updates need PBL 9+.
- **Verify.** `facts.play_billing`. RevenueCat Flutter/RN 9.0+ ships PBL 8. `in_app_purchase_android` is read from its Gradle file in the pub cache. Check which PBL the plugin's next major ships before planning the PBL 9 move.
- **Fix.** Upgrade the plugin (`purchases_flutter` ≥ 9, `in_app_purchase` latest). For PBL 8 migrate the removed APIs (`querySkuDetailsAsync`, the no-arg `enablePendingPurchases()`, `queryPurchaseHistory`). PBL 9 returns `BILLING_UNAVAILABLE` when the Play Store is blocked and makes `getLinkUri()` nullable.

### AND-PERM-*: Permissions and APIs that Access Sensitive Information
Check each against the app's **core** purpose. Ads, analytics or "nice to have" never justify a restricted permission.

| Permission | Rule | Fix |
|---|---|---|
| `READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `READ_CALL_LOG`, `WRITE_CALL_LOG`, `PROCESS_OUTGOING_CALLS` | Only default SMS/dialer handlers or approved exceptions with a Permissions Declaration. Call-log verification ends 2027-01-27 | SMS Retriever API, SMS User Consent API, Digital Credentials API. Remove with `tools:node="remove"` if a plugin adds it |
| `MANAGE_EXTERNAL_STORAGE` | All files access only for file managers, backup, antivirus, document managers | SAF (`ACTION_OPEN_DOCUMENT`), MediaStore, app-specific dirs |
| `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO` | Only for apps whose core use is broad media access. One-off picks must use the Photo Picker. Needs a declaration | `image_picker` ≥ 1.0 on Android uses the Photo Picker, so drop the permission |
| `ACCESS_BACKGROUND_LOCATION` | Declaration, demo video, prominent disclosure that says "location" and "when the app is closed or not in use" | Foreground-only, or a WorkManager/Geofence API design |
| `ACCESS_FINE_LOCATION` | Play Console declaration for every app from 2027-01-27. For targetSdk 37+ the location button is mandatory for one-time precise location | `ACCESS_COARSE_LOCATION` if city level is enough. Button-only apps add `android:usesPermissionFlags="onlyForLocationButton"` |
| `READ_CONTACTS` | Contact Picker for targetSdk 37+ apps without a core need (2027-01-27) | Android Contact Picker intent |
| `WRITE_CONTACTS`, `MANAGE_CONTACTS` | Direct writes stop at targetSdk 38. `MANAGE_CONTACTS` is restricted to contact managers, dialers, caller ID, sync and backup apps (2027-08-25) | `ACTION_INSERT` / `ACTION_INSERT_OR_EDIT` intents need no permission |
| `ACCESS_LOCAL_NETWORK`, `NEARBY_WIFI_DEVICES` | Local network access only when device pickers are not enough. Declaration for targetSdk 37+ (2027-08-25) | `NsdManager` device picker, Cast Output Switcher |
| `QUERY_ALL_PACKAGES` | Only with core need and a declaration | `<queries>` with specific packages or intents |
| `REQUEST_INSTALL_PACKAGES` | Only if installing packages is the core function | Remove (often added by an OTA or file plugin) |
| `USE_EXACT_ALARM` | Only alarm clocks and calendars | `SCHEDULE_EXACT_ALARM` with the runtime grant, or inexact alarms |
| `SCHEDULE_EXACT_ALARM` | User-granted, denied by default on Android 14+. Must degrade gracefully | Check `canScheduleExactAlarms()`, fall back to inexact |
| `USE_FULL_SCREEN_INTENT` | Calls and alarms only, otherwise a declaration and a user grant | Normal high-priority notification |
| `BIND_ACCESSIBILITY_SERVICE` | Accessibility API declaration, prominent disclosure, `android:isAccessibilityTool` only for real accessibility tools | |
| `BIND_VPN_SERVICE` | See AND-VPN-SERVICE | |
| `FOREGROUND_SERVICE_*` | Declare each type in Play Console with a video. `dataSync` often belongs in WorkManager. Location FGS for geofencing ends 2027-01-27 | Geofence API, WorkManager, Media3 for playback |
| `BODY_SENSORS` | Replaced on Android 16 by `android.permission.health.*` (for example `READ_HEART_RATE`). Needs the Health Connect rationale activity | Migrate to Health Connect permissions |
| `AD_ID` | Declare in Data safety. Must be removed when the target audience is children only | `tools:node="remove"` |
| `RECORD_AUDIO`, `CAMERA`, `ACTIVITY_RECOGNITION` | Not restricted, but must be in Data safety, and a prominent disclosure is needed when use is not obvious | |

Plugins add permissions through manifest merging. If `facts.android_merged_manifest` is null, say so and ask for a release build's merged manifest (`build/app/intermediates/merged_manifest/release/`) or read the plugins' manifests.

**Personal loan, Earned Wage Access and loan calculator apps** may not request any of `READ_EXTERNAL_STORAGE`, `WRITE_EXTERNAL_STORAGE`, `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO`, `READ_CONTACTS`, `ACCESS_FINE_LOCATION`, `READ_PHONE_NUMBERS`, `QUERY_ALL_PACKAGES`. If the app lends money, any of these is CRITICAL. Loans repaid in full within 60 days are banned, and US APR must stay below 36%.

### AND-FGS-LOCATION: Foreground service policy
See the table. Plan the Geofence API migration before 2027-01-27.

### AND-16KB-PAGE: 16 KB page size (2027-02-01)
- **Rule.** Apps targeting Android 15+ that ship native libraries must be 16 KB aligned. From 2027-02-01 updates that are not cannot be released.
- **Verify.** Native code present (`.so` files, NDK/CMake config, plugins with native code: most Flutter apps have it through the engine and plugins). Android Gradle Plugin below 8.5.1, NDK below r28, or `useLegacyPackaging true` for `jniLibs`.
- **Fix.** AGP ≥ 8.5.1, NDK ≥ r28 (or `-Wl,-z,max-page-size=16384`), current plugin versions, then check the AAB in App bundle explorer, which flags unaligned libraries.

### AND-EDGE-TO-EDGE, AND-PREDICTIVE-BACK, AND-ORIENTATION-LOCK: Android 16 behaviour
Not policy rules, but every update now targets 36 and these break the UI the reviewer and users see.
- **Edge-to-edge.** `windowOptOutEdgeToEdgeEnforcement` is ignored on Android 16. Handle insets (Flutter `SafeArea` / `MediaQuery.padding`, RN `react-native-safe-area-context`).
- **Predictive back.** `onBackPressed` is not called and `KEYCODE_BACK` is not dispatched. Flutter `WillPopScope` → `PopScope`, Android `OnBackPressedCallback`. `android:enableOnBackInvokedCallback="false"` is a temporary opt-out.
- **Large screens (sw ≥ 600dp).** `screenOrientation`, `resizeableActivity="false"`, `minAspectRatio`, `maxAspectRatio` and `setRequestedOrientation()` are ignored. Flutter `SystemChrome.setPreferredOrientations` is ignored there too. Games are exempt with `android:appCategory="game"`. The `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` opt-out **stops working at targetSdk 37**.
- **Fix.** Test on a tablet or foldable emulator in landscape. Make layouts adapt instead of locking orientation.

### AND-MINIFY-OFF: technical quality (Feb 2027)
- **Rule.** When DEX is over 10 MB (games 50 MB), obfuscation, optimization and shrinking must each reach 25%. Missing it means reduced visibility, then publishing limits.
- **Verify.** `minifyEnabled false` / `isMinifyEnabled = false` in the release build type, `-dontobfuscate`, `-dontoptimize`, `-dontshrink`, a broad `-keep class **`, or RN `enableProguardInReleaseBuilds = false` (the RN default).
- **Fix.** Enable R8 (full mode) in release and narrow keep rules. Check DEX size and percentages in App bundle explorer.

### AND-RESTORE-CREDENTIALS: zero-tap sign-in (April 2027)
- **Rule.** Every app with sign-in, optional or mandatory, must bring back the signed-in state when the user moves to a new device. Restore Credentials API is the recommended path. Block Store only counts if it was in production by 2026-09-30. Guests come back as guests. Regulated finance and health apps can ask for an exemption in Play Console.
- **Verify.** Sign-in present (`facts.sdk_categories.third_party_login`, `account_backend`) and no `androidx.credentials` restore credential (`CreateRestoreCredentialRequest`, `GetRestoreCredentialOption`). `android:allowBackup="false"` or data extraction rules that exclude everything also block the transfer path.
- **Fix.** After sign-in create a restore credential holding an opaque key or refresh token. On first launch read it and exchange it on the server. Delete it on sign-out.

### AND-LEGACY-GSI, AND-SAFETYNET: deprecated Google APIs
- **Legacy Google Sign-In.** `GoogleSignIn`, `GoogleSignInClient` and One Tap `beginSignIn` are deprecated and will be removed from the Play services Auth SDK. No date yet, so report as SUGGESTION. Move to Credential Manager (`androidx.credentials` + `googleid`). Flutter `google_sign_in` 7 moved to Credential Manager.
- **SafetyNet Attestation** no longer works. Any `play-services-safetynet` or `SafetyNet.getClient(` call fails. Replace with the Play Integrity API (`com.google.android.play:integrity`). IMPORTANT when it guards login or payments.

### AND-VPN-SERVICE: VpnService policy
- **Rule.** VpnService only when VPN is the core function, or for parental control, enterprise/MDM, device security, network tools, browsers or carrier apps. Encrypted tunnel, no traffic manipulation for monetization, prominent disclosure for any data collection. Play Console declaration with a video, documented in the listing, **organization account** required.
- **Verify.** `<service android:permission="android.permission.BIND_VPN_SERVICE">`, `extends VpnService`, plugins such as `flutter_vpn`, `openvpn_flutter`, `wireguard_flutter`. Ad blockers and "data saver" SDKs often embed one.

### AND-SIDELOAD-FLAVOR: developer verification
- **Rule.** Package names distributed only outside Play (a Huawei, F-Droid or direct-APK build with its own `applicationId`) must be registered for Android developer verification. Enforcement is live in four countries and global in 2027.
- **Verify.** `productFlavors` with `applicationIdSuffix` or a different `applicationId`.
- **Fix.** Register each package name in Play Console or the Android Developer Console.

### AND-CLEARTEXT: Data safety
Data safety's "data is encrypted in transit" answer is false with cleartext traffic. Use a network security config that allows only the hosts that need it.

### X-ACCOUNT-DELETION: User Data policy, account deletion
- **Rule.** Apps that let users create accounts must offer deletion **inside the app** and through a **web link** declared in the Data safety form, which works without reinstalling. The data must be deleted (or the retention explained).
- **Fix.** In-app flow plus a public page (`https://<domain>/delete-account`) that takes a request without the app.

### X-AI-DATA-SHARING: User Data policy (2026-07-15 clarification)
- **Rule.** The developer is responsible for data sent to third-party AI: limited use, prominent disclosure, consent, Data safety declaration (shared with third parties).
- **Fix.** Same consent sheet as for Apple 5.1.2(i). Declare "User content → shared" in Data safety. Check the provider's data-use terms (no training on user data).

### X-AI-IMAGERY: AI-Generated Content policy, Inappropriate Content
- **Rule.** Generative AI apps must prevent restricted content (sexual content, NCII, CSAM, deceptive deepfakes of real people), give users an in-app way to report or flag offensive output, and use those reports to improve filtering.
- **Fix.** Prompt and output filtering, an in-app report button on each output, a review process. Check the app does not market "undress" or "face swap anyone".

### X-UGC-MODERATION, X-UGC-PRESENT, X-ANON-CHAT: User Generated Content, Child Safety Standards, Families
- **Rule.** UGC apps need terms that forbid objectionable content, in-app reporting of content and users, blocking, and real moderation. Social and dating apps must publish **Child Safety Standards** (CSAE) and a contact in Play Console, offer in-app feedback, and act on CSAM. Since 2026-08-26 anonymous and random chat apps fall under Child Endangerment and Age-Restricted Content rules and may not target children. Dating apps must block minors with the Console tools.
- **Fix.** Report and block on every UGC surface, a moderation queue, a public CSAE standards page linked in Play Console, and the target audience set to 18+ (or 13+ with age-appropriate controls) for anonymous chat.

### X-IAP-RESTORE, X-PAYWALL-TERMS, X-EXTERNAL-PAYMENT: Payments, Subscriptions
- **Rule.** Digital goods through Play Billing (user-choice, alternative billing and external links only in eligible programmes and regions). Subscription offers must state price, period, renewal and how to cancel. No misleading free-trial UI. Eligibility-based discounts state criteria, verification and the price afterwards (2027-01-27). Digital purchases made through AI or agentic flows follow the same Payments policy (29 Oct 2026 guidance).
- **Fix.** Show the base plan price and period from `ProductDetails`, trial length and what happens after it, a Manage subscription link (`https://play.google.com/store/account/subscriptions`).

### X-REVIEW-MODE-SWITCH, X-HIDDEN-FEATURE, X-REMOTE-FEATURE-GATES, X-CODE-PUSH: Deceptive Behavior, Device and Network Abuse
- **Rule.** Apps may not behave differently during review, manipulate the review process (restated 29 Oct 2026), hide functionality or download executable code from outside Google Play that changes the app (interpreted code in a sandbox, e.g. JS in a WebView, is allowed).
- **Fix.** As for Apple 2.5.19. OTA patches only for fixes.

### X-WEBVIEW-WRAPPER, X-PLACEHOLDER: Minimum functionality, Webviews and Affiliate Spam
- **Rule.** Apps must offer a stable, responsive, engaging experience. Apps whose main purpose is to show a website you do not own are spam.

### X-KIDS-AUDIENCE: Families policy
- **Rule.** If children are in the target audience: only Families Self-Certified ad SDKs, no AD_ID at API 33+, no device identifiers (AAID, SIM serial, Build serial, BSSID, MAC, SSID, IMEI, IMSI), no location permissions, no phone number via `TelephonyManager`, parental-gated purchases and links, content and ads suitable for children. Mixed-audience apps use non-certified SDKs only behind a neutral age screen.
- **Certified SDKs (minimum versions, 2026-11-05).** `play-services-ads` 19.0.0 (Flutter `google_mobile_ads`), `play-services-pal` 18.0.0, IMA `interactivemedia` 3.25.1, `unity-ads` 4.0.1, `vungle publisher-sdk-android` 6.10.4, `inmobi-ads` 10.5.5, `chartboost-sdk` 9.1.1, `fyber marketplace-sdk` 8.2.1, `HyprMX-SDK` 6.0.3, `kidoz-android-native` 8.9.4, `superawesome` 8.4.3, `AATKit-family-safe` 3.0.3, `adcolony` 4.8.0. **ironSource/LevelPlay, AppLovin, Meta Audience Network, Mintegral, Pangle and Liftoff are not on the list.**

### X-HEALTH-DATA: Health apps, Health Connect
- **Rule.** Health apps declaration in Play Console, Health Connect permission declaration with a privacy policy shown through the rationale activity, medical disclaimers, no ad use, **organization account**. On Android 16 `BODY_SENSORS` moves to `android.permission.health.*`.

### X-PERIODIC-SENSING: User Data, prominent disclosure
- **Rule.** Collecting audio, camera or location data in a way the user would not expect needs a prominent in-app disclosure and consent before collection, and the Data safety form must list it. Background microphone use also requires a `microphone` foreground service type on Android 14+.
- **Fix.** Opt-in setting with a disclosure, visible indicator, stop when not in the foreground, declare in Data safety.

### X-ADS-PRESENT: Ads policy
- **Rule.** No ads that interfere with use, hidden close buttons, full-screen interstitials on app launch or exit without a natural break, ads on lock screens, or ads disguised as app content. Ad SDK data goes into Data safety (Device or other IDs, App activity, shared for advertising).

---

### EXPO-MANAGED: scan coverage
Managed Expo apps have no `ios/` or `android/` until build time, so only `app.json` was read. For a full check run `npx expo prebuild --no-install` in a scratch copy and scan that copy. `targetSdk` comes from the Expo SDK default or `expo-build-properties`.

---

## Beyond the scanner (always list under Manual checks if relevant)

- **Data safety form** matches `facts.sdk_categories` and the permissions: ads → device IDs shared, analytics → app activity, crash reporting → diagnostics, AI → user content shared, location → precise or approximate (July 2026 guidance).
- **Content rating** questionnaire done (unrated apps are not allowed) and consistent with UGC and AI features.
- **Target audience and content**, Families self-certification if under 13.
- **Organization account** for finance (banking, loans, trading, crypto), health, VPN and government apps.
- **Financial features declaration** for any app with a financial feature. Crypto exchange and wallet country rules (Hong Kong VATP since 29 Oct 2026). News & Magazines declaration.
- **Trader status** declared by 2027-02-01, with a Terms of Service URL per app for traders.
- **Play Age Signals.** Required in practice for apps in scope of US state age laws (Texas SB 2420 is in effect). Age data may only be used for age-appropriate experiences, never ads or analytics. Use API 0.0.4+.
- **App access**: demo credentials for login-gated apps, in the App content page.
- **16 KB page size**: check the AAB in App bundle explorer.
- **Account deletion web link** filled in Data safety.
- **Store listing**: no misleading claims, no ranking or "best" claims, screenshots of the real app, AI features labelled honestly.
- **Japan** payment authorization by 2026-12-01 when selling to or from Japan.
- **Native Java/Kotlin apps**: Google's `play-policy-insights` skill (github.com/android/skills) adds deeper Data-safety source/sink tracing.
