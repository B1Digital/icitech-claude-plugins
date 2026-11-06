# Apple App Review Guidelines: what to check in code

Rules as of **2026-11-05**. Sources: https://developer.apple.com/app-store/review/guidelines/
(page last updated 16 October 2026), Apple Developer News, Upcoming Requirements
(developer.apple.com/news/upcoming-requirements/), the age assurance Q&A and the
third-party SDK requirements page. Guideline numbers as Apple writes them.

## In force and upcoming

| Date | Change | Why it matters in code |
|---|---|---|
| since 2025-02-12 | Listed third-party SDKs must ship a privacy manifest, binary ones must be signed (ITMS-91061, ITMS-91065) | Old or discontinued plugins fail upload |
| since 2026-01-31 | New age ratings **4+, 9+, 13+, 16+, 18+** and the full questionnaire. Unanswered = update blocked | Each capability has a minimum rating (see Age rating) |
| 2026-02-06 | **1.2** covers random or anonymous chat. Apps used **primarily** for it "do not belong on the App Store and may be removed without notice" | Moderation does not rescue a primarily anonymous chat app |
| since 2026-04-28 | Uploads must be built with **Xcode 26 / iOS 26 SDK** | CI images and pinned Xcode versions |
| 2026-05 → 07 | Utah (2026-05-06), Texas SB 2420 (2026-06-04), Louisiana (2026-07-01) age laws for new accounts. **Declared Age Range API** where legally required, **also for 18+ apps** | Social, chat, dating and 18+ apps |
| 2026-06-08 | **4.3(a)/(b)** spam rewrite. Saturated categories need a "meaningfully different or improved experience". **4.5.3** names Live Activities as a spam channel. **1.2** failure to keep safeguards can breach the Developer Code of Conduct | White-label apps from one codebase |
| since 2026-09-09 | Minimum deployment target **iOS 13** | `IPHONEOS_DEPLOYMENT_TARGET`, Podfile `platform :ios` |
| 2026-09-16 | EU alternative ATT prompt from iOS 27.2. In Germany, France, Italy, Poland and Romania only the alternative prompt is available | No compliance change, wrappers may lag |
| 2026-10-01 | One set of EU terms (Attachment 14). Kids apps: no link-outs, parental gate on alternative payments | |
| 2026-10-16 | **1.2** covers nonconsensual intimate imagery (NCII), including AI-generated. **2.5.19** clarifies that hidden, dormant or undocumented features, including features hidden "through code obfuscation or other methods", mean removal and **developer account termination**. New **2.3.14** creative assets | Review-mode switches, remote-config gates, AI image features |
| 2026-11-16 → **2027-01-12** | Age-rating questionnaire adds **Shared Location** and **Dating and Relationships** (includes AI romantic companions). Dating forces **18+**. Every app must answer by 2027-01-12 | Location sharing between users, dating, AI companion personas |
| early 2027 | **Regulated medical device** declaration for Health & Fitness and Medical apps in EU, UK and US. Without it, updates stop | HealthKit, symptom or dosage features |
| April 2027 | Uploads built with the **iOS 27 SDK** (Xcode 27). **iPhone Duo** screenshots required | CI toolchain, metadata |
| spring 2027 | Siri AI (App Intents) submissions open. Beta-SDK builds cannot be submitted | Keep 27.3 beta code out of release |

Still in force and frequently hit: 5.1.2(i) third-party AI disclosure (Nov
2025), 5.1.1(v) account deletion, 4.8 login services, privacy manifests
(ITMS-91053), 2.5.18 ads, 3.1.x payments, 4.7 mini apps and chatbots.

---

## Findings by scanner ID

### X-REVIEW-MODE-SWITCH, X-REMOTE-FEATURE-GATES, X-HIDDEN-FEATURE: 2.5.19, 2.3.1
- **Rule.** "Don't include any hidden, dormant, or undocumented features in your app." Hiding them, "such as through code obfuscation or other methods", is grounds for removal and termination of the developer account. Apple calls this a clarification of long-standing policy (formerly 2.3.1), but the consequence is account-level. **2.3.1(a)** still requires new features to be described "with specificity" in the Notes for Review.
- **Verify.** Read the flag. Does it hide functionality during review (`isReviewMode`, a server flag set while "in review", a build-number check)? Does a remote-config bool enable a whole feature that is off by default? Is the hidden menu reachable in release (not behind `kDebugMode`, `__DEV__`, `#if DEBUG`)?
- **Not a finding.** Build obfuscation on its own (Flutter `--obfuscate`, R8, Hermes bytecode). It only matters when it hides an undocumented feature. Features **downloaded** later are 2.5.2 (see X-CODE-PUSH).
- **Risk.** CRITICAL for anything that changes behaviour for reviewers.
- **Fix.** Remove review-mode logic entirely. Ship remote-config features **on** in the reviewed build (staged rollout is fine if the reviewer can reach the feature) and describe each one specifically in the App Review notes. Keep kill switches (turning a feature *off*) and A/B tests of existing features. Gate debug menus with `kDebugMode`/`__DEV__` so tree-shaking removes them.

### X-CODE-PUSH: 2.5.2, 3.3.1(b) (Developer Program License Agreement)
- **Rule.** Apps may not download code that "introduces or changes features or functionality". Interpreted code is allowed only if it does not change the app's primary purpose or add features.
- **Verify.** Which OTA tool (Shorebird, CodePush, expo-updates, server-driven UI such as rfw/stac). Has it been used for features in the past (git log of patch releases)?
- **Fix.** Use OTA only for bug fixes. Put new features through review.

### X-AI-IMAGERY: 1.2 (2026-10-16)
- **Rule.** Apps must proactively prevent and remove nonconsensual intimate imagery, including AI-generated. Failure to act after notice means removal.
- **Verify.** What does the generator accept (user photos of real people, face swap, "try on", undress-style edits)? Is there a prompt filter and an output classifier? Can users report a generated image?
- **Fix.** Block sexual or nude edits of real-person photos at the prompt and the output (provider safety settings plus your own classifier). Add in-app reporting on every generated image, a takedown process with a response time, and published contact info. Document the safeguards in the review notes.

### X-AI-DATA-SHARING: 5.1.2(i)
- **Rule.** "You must clearly disclose where personal data will be shared with third parties, including with third-party AI, and obtain explicit permission before doing so."
- **Verify.** What reaches the AI provider (user text, photos, voice, profile)? Is there a consent screen **before** the first call that names the provider or "third-party AI", and is the choice stored? Server-side calls count too.
- **Fix.** A one-time consent sheet before the first AI request: what is sent, to whom, why, with Accept and Not now. Block the feature until accepted, allow withdrawal in settings, and update the privacy policy and the App Privacy label.

### X-UGC-MODERATION, X-UGC-PRESENT: 1.2, 1.2.1
- **Rule.** UGC apps (including AI content apps) need: a filter for objectionable material, a report mechanism with timely response, the ability to block abusive users, and published contact information. Creator apps need an age restriction for content above the app's rating (1.2.1(a)), based on verified or declared age.
- **Verify.** Find report and block UI on every UGC surface (posts, comments, profiles, messages). Is there server-side filtering? Does blocking actually hide content?
- **Fix.** Add Report and Block on each item and profile, a profanity or ML filter at write time, an admin queue with action inside 24 hours, a contact email in settings and on the listing. Update the age-rating answers (user-generated content, messaging and chat, social media).

### X-ANON-CHAT: 1.2 (2026-02-06)
- **Rule.** Apps "used primarily for … Chatroulette-style experiences, random or anonymous chat … do not belong on the App Store and may be removed without notice."
- **Verify.** Is anonymous or random matching the main purpose, or a secondary feature?
- **Fix.** Primary purpose: moderation is not a remedy. Redesign around known identities. Secondary feature: all four 1.2 safeguards plus an 18+ rating or a Declared Age Range gate.

### X-SIGN-IN-WITH-APPLE: 4.8
- **Rule.** If the app uses a third-party or social login for the primary account, it must also offer a login that limits data to name and email, lets the user hide their email, and does not track without consent. Sign in with Apple satisfies this.
- **Exempt.** Only your own account system, alternative app marketplace login, education or enterprise accounts, government or industry ID, clients for a specific third-party service.
- **Fix.** Add `sign_in_with_apple` (Flutter), `expo-apple-authentication` / `@invertase/react-native-apple-authentication` (RN), with equal prominence on the login screen.

### IOS-SIWA-ENTITLEMENT, X-SIWA-REVOKE: 2.1, 5.1.1(v)
- **Verify.** `com.apple.developer.applesignin` in the entitlements. On account deletion, the backend calls `https://appleid.apple.com/auth/revoke` with the user's refresh token or authorization code.
- **Fix.** Revoke at deletion time with a fresh authorization code. Flutter + Firebase: run a new `SignInWithApple.getAppleIDCredential(...)` (package `sign_in_with_apple`) in the delete flow and pass `credential.authorizationCode` to `FirebaseAuth.instance.revokeTokenWithAuthorizationCode(...)`, then delete the user. Do not take the code from `reauthenticateWithProvider(AppleAuthProvider())`: a cancelled sheet there can leave the provider stuck. Custom backends: exchange the code at `/auth/token` for a refresh token and call `/auth/revoke`.

### X-SIWA-RELAY-DOMAIN: 4.8, 2.1
- **Rule.** New Sign in with Apple relay addresses use **`private.icloud.com`**. Existing `privaterelay.appleid.com` addresses keep working. A validator, allowlist or "is relay" helper that only knows the old domain rejects new users.
- **Fix.** Accept both domains everywhere. Keep `icloud.com` (Hide My Email) handling separate. Test sign-up with a new relay address.

### X-ACCOUNT-DELETION: 5.1.1(v)
- **Rule.** "If your app supports account creation, you must also offer account deletion within the app." Deactivation alone is not enough. Asking users to email or call is only acceptable for highly regulated industries. Social logins must also be revocable in-app, and social-network tokens may not be stored off the device.
- **Verify.** A reachable Delete Account action (usually Settings, Profile, Account) that deletes server data, not just signs out. Institution-provisioned accounts (SSO, school, employer) with no sign-up are exempt, so downgrade if you see none.
- **Fix.** Settings → Delete account → confirm → backend deletes or anonymises user data, revokes Sign in with Apple, cancels nothing automatically but tells the user how to cancel subscriptions.

### X-PRIVACY-POLICY-LINK: 5.1.1(i)
- **Rule.** Privacy policy link in App Store Connect **and inside the app**, easy to reach.
- **Fix.** A Privacy Policy row in settings and on the sign-up and paywall screens.

### IOS-USAGE-STRING-MISSING, IOS-USAGE-STRING-WEAK: 5.1.1(ii), 2.1, ITMS-90683
- **Rule.** Purpose strings must say clearly why the data is needed, ideally with an example. A missing key crashes the app at the permission call and fails upload (ITMS-90683) when a linked plugin references the API, even if the app never calls it. A key that exists only in `InfoPlist.strings` counts as missing. Extensions need keys in their own `Info.plist`. Generic text ("This app needs camera access") is a common rejection.
- **Incomplete strings.** A string that is specific but leaves out a real use (it names voice notes but the app also listens for song recognition) is also a 5.1.1(ii) problem. Check every call site of the API against the text.
- **Fix.** "Camera is used to scan the QR code on your ticket." Cover every use. Localise the strings (`InfoPlist.strings`). Do not request a permission before the user reaches the feature.

### IOS-PERMISSION-HANDLER-MACROS: 2.1
- **Rule.** Not a guideline by itself, but the reviewer sees a feature that never works. `permission_handler` compiles each iOS permission out unless the matching `PERMISSION_*=1` macro is set in the Podfile `post_install`.
- **Fix.** In `ios/Podfile` → `post_install` → `GCC_PREPROCESSOR_DEFINITIONS`, add `'PERMISSION_CAMERA=1'` etc. for every `Permission.x` the Dart code requests.

### IOS-ATT, IOS-PRIVACY-MANIFEST-TRACKING: 5.1.2(i), 2.5.18
- **Rule.** Tracking (linking data with third parties for ads or measurement, IDFA) requires the App Tracking Transparency prompt. You may not require users to enable tracking, notifications or location to use features or earn rewards (5.1.2(i)).
- **Verify.** Ad or attribution SDK present (wrapper packages count), the prompt is shown before the SDK initialises or loads ads (`requestTrackingAuthorization` natively, `AppTrackingTransparency.requestTrackingAuthorization()` or `Permission.appTrackingTransparency.request()` in Flutter, `requestTrackingPermissionsAsync()` in Expo), `NSUserTrackingUsageDescription` set, `NSPrivacyTracking` and `NSPrivacyTrackingDomains` in the privacy manifest.
- **Fix.** Call ATT once after the first screen is visible and before initialising ads. Without consent, ads must still work as non-personalised. The purpose string and any pre-prompt may not offer rewards ("allow tracking to earn credits" is a 5.1.2(i) rejection).
- **NSPrivacyTracking.** `true` (with `NSPrivacyTrackingDomains`) when the app or its SDKs track in Apple's sense: linking app data with third-party data for targeted ads or ad measurement, or sharing it with a data broker. Ad SDKs that use IDFA after ATT consent do. `false` is only correct when nothing tracks, for example ads served contextually without IDFA.

### IOS-PRIVACY-MANIFEST, IOS-PRIVACY-MANIFEST-NOT-IN-TARGET, IOS-PRIVACY-MANIFEST-INVALID: 5.1.1, ITMS-91053, ITMS-91056
- **Rule.** Required-reason APIs (UserDefaults, file timestamps, system boot time, disk space, active keyboards) need a declared reason in a privacy manifest (ITMS-91053). A manifest with unknown keys or reason codes fails upload (ITMS-91056). The app's manifest describes **only the app's own** API use and collection. SDKs bring their own.
- **Fix.** `ios/Runner/PrivacyInfo.xcprivacy`, added to the Runner target. `NSPrivacyAccessedAPIType` must be one of `NSPrivacyAccessedAPICategoryUserDefaults`, `…FileTimestamp`, `…SystemBootTime`, `…DiskSpace`, `…ActiveKeyboards`, each with valid reason codes (for example `CA92.1`, `C617.1`, `35F9.1`, `E174.1`).

### IOS-SDK-MANIFEST-RISK: ITMS-91061, ITMS-91065
- **Rule.** New apps, and updates that **add** one of Apple's listed SDKs, must include that SDK's privacy manifest. Binary SDKs on the list must be signed. The list (86 entries) includes Flutter itself and plugins such as `connectivity_plus`, `device_info_plus`, `file_picker`, `flutter_inappwebview`, `flutter_local_notifications`, `fluttertoast`, `geolocator_apple`, `image_picker_ios`, `package_info`, `package_info_plus`, `path_provider`, `share_plus`, `shared_preferences_ios`, `sqflite`, `url_launcher`, `video_player_avfoundation`, `wakelock`, `webview_flutter_wkwebview`, plus Firebase, GoogleSignIn, FBSDK, OneSignal, Realm, SDWebImage, Alamofire, Lottie, hermes, Capacitor and Cordova.
- **Verify.** Discontinued packages that never got a manifest (`package_info`, `wakelock`, very old `*_ios` split packages). Vendored `.xcframework` / `.framework` without `_CodeSignature/`.
- **Fix.** `package_info` → `package_info_plus`, `wakelock` → `wakelock_plus`, update the rest to current versions, get signed binaries from the vendor.

### IOS-DEPLOYMENT-TARGET, IOS-XCODE-PINNED-OLD: upload floors
- **Rule.** Since 2026-04-28 uploads are built with Xcode 26 and the iOS 26 SDK. Since 2026-09-09 iOS apps must target iOS 13 or later. From April 2027 the iOS 27 SDK is required.
- **Verify.** `IPHONEOS_DEPLOYMENT_TARGET` in `project.pbxproj`, `platform :ios` in the Podfile, `expo-build-properties` `ios.deploymentTarget`. Pinned Xcode in `.xcode-version`, GitHub Actions (`xcode-version:`, `setup-xcode`, old `macos-13`/`macos-14` images), `codemagic.yaml`, `eas.json` images, fastlane `xcversion`.
- **Fix.** Deployment target ≥ 13.0. Pin CI to Xcode 26.x now and plan Xcode 27 before April 2027.

### IOS-BACKGROUND-MODES: 2.5.4
- **Rule.** Background audio only for audible playback, location only for navigation or fitness-type features, VoIP only for calls.
- **Fix.** Remove unused modes. Explain the used ones in the review notes.

### IOS-ADS-IN-EXTENSION, X-ADS-PRESENT: 2.5.18, 2.5.16
- **Rule.** Ads only in the main app: not in extensions, App Clips, widgets, notifications, keyboards or watchOS apps. Ads must fit the app's age rating and may not be targeted on sensitive data (HealthKit, ClassKit) or at kids. Interstitials must be clearly marked, have visible close or skip buttons and must not trick users into tapping. Users must be able to see targeting info and report inappropriate ads.
- **Verify.** Podfile target blocks or SPM dependencies of widget, extension and App Clip targets that pull an ad SDK.

### IOS-VPN: 5.4, 5.5
- **Rule.** VPN apps use `NEVPNManager`, come from an **organization** account, show a data-collection declaration **before** purchase or use, never sell or share data, and give licence info where a territory requires it. MDM needs Apple's capability.
- **Verify.** `com.apple.developer.networking.networkextension` or `vpn.api` entitlements, `NEPacketTunnelProvider` targets, VPN plugins. Ad or analytics SDKs inside a VPN app are a red flag.

### X-IAP-RESTORE, X-PAYWALL-TERMS, X-EXTERNAL-PAYMENT: 3.1.1, 3.1.2, 3.1.3
- **Rule.** Digital content and features must be sold through IAP. Purchased credits must not expire. A restore mechanism is required for restorable products. Subscriptions: at least 7 days, available on all the user's devices, and the paywall must state what the user gets, the price, the period and auto-renewal, with Terms of Use (EULA) and Privacy links.
- **External links by storefront.** On the **United States** storefront, buttons, external links and other calls to action need **no entitlement** (3.1.1(a), 3.1.3). The EU/EEA (External Purchase Link, alternative PSP), Japan (Custom Link Regions, IAP shown at the same time), Brazil, South Korea, the Netherlands (dating) and Russia each need their own entitlement and Info.plist keys (`SKExternalPurchase`, `SKExternalPurchaseLink`, `SKExternalPurchaseCustomLinkRegions`, `SKExternalPurchaseLinkStreamingRegions`). Everywhere else the ban stands.
- **Fix.** Restore Purchases on the paywall and in settings. Show price per period from StoreKit, renewal text, Terms and Privacy links. Gate "buy on web" by storefront: US allowed, entitled regions through `ExternalPurchaseLink.canOpen` / `ExternalPurchaseCustomLink.isEligible`, everywhere else no link. Never hard-code a link-out for all storefronts.

### X-LOOT-BOX: 3.1.1
- **Rule.** Paid randomized items must disclose the odds of each item type **before** purchase. Loot boxes rate 9+ globally, 16+ in Australia, 18+ in Brazil.
- **Fix.** An odds table on the purchase screen and the loot-box answer in the questionnaire.

### X-CUSTOM-REVIEW-PROMPT: 5.6.1, 3.2.2(x)
- **Rule.** Use the system API to ask for reviews. Custom review prompts are not allowed, nor is review gating (sending happy users to the store and unhappy ones to a form) or rewarding reviews.
- **Fix.** `SKStoreReviewController` / `AppStore.requestReview(in:)`, Flutter `in_app_review` `requestReview()`, Expo `expo-store-review`, at natural moments.

### X-AGE-ASSURANCE, X-AGE-RATING-INPUTS: age rating, 1.2.1(a), 4.7.5, 5.1.4
- **Rule.** In regions where the law requires it (Texas, Utah, Louisiana, Brazil, Australia), apps must check age with the **Declared Age Range API**, even 18+ apps. Significant updates must be blocked for minors until a parent consents, and a `RESCIND_CONSENT` server notification stops the app. "Social media disabled for users under 13" in the questionnaire requires the API.
- **Minimum ratings from the questionnaire.** Loot boxes 9+. Social media 13+. Infrequent simulated gambling and frequent contests 13+. **Unrestricted web access 16+.** Frequent medical information 16+. Gambling and frequent simulated gambling 18+. **Dating and Relationships 18+** (from 2026-11-16). Australia: social media and loot boxes 16+. Brazil: loot boxes 18+, Shared Location A16.
- **Verify.** `com.apple.developer.declared-age-range` entitlement, `DeclaredAgeRange` / `AgeRangeService` calls or a wrapper package (`age_range_signals`). A self-typed birth date as the only age check in a social, chat, dating or 18+ app is a red flag. A birth date for COPPA or GDPR alone is allowed (5.1.4).
- **Fix.** Add the capability, call the API on first launch where required, change features by age band, handle `RESCIND_CONSENT`. Re-answer the questionnaire whenever a listed capability is added.

### X-WEBVIEW-WRAPPER: 4.2, 4.2.2
- **Rule.** Apps that are mainly a repackaged website, or offer no lasting value, are rejected. 4.3 saturated categories need a clear differentiator. A free URL bar counts as unrestricted web access (16+).
- **Fix.** Native navigation, offline state, push, device features. Or ship as a web app.

### X-PLACEHOLDER: 2.1(a), 2.3.3
- **Rule.** No placeholder text, empty screens or "coming soon" features in the submitted build.
- **Fix.** Hide unfinished entries (they can come back in an update that goes through review).

### X-KIDS-AUDIENCE: 1.3, 5.1.4
- **Rule.** Kids Category apps: no third-party analytics or ads (narrow exceptions), parental gate before links, purchases and permission prompts, no external purchase links in the EU and Japan. Apps "for kids" outside the category still follow COPPA, GDPR-K and local law. Names may only say "For Kids" or "For Children" inside the Kids Category.
- **Fix.** Remove ad and analytics SDKs or move to first-party, add a parental gate, check the age range.

### X-HEALTH-DATA: 5.1.3, 1.4.1, 1.4.2
- **Rule.** HealthKit data may not be used for ads or stored in iCloud. Medical apps must remind users to consult a doctor. Vitals measured with device sensors alone (blood pressure, glucose, SpO₂, temperature, x-ray) are not allowed. Dosage calculators only from an approved entity. Health & Fitness and Medical apps in the EU, UK and US declare their **regulated medical device** status in App Store Connect, or updates stop in early 2027.

### X-PERIODIC-SENSING: 2.5.14, 5.1.1(ii)
- **Rule.** Recording or sampling the microphone, camera or location must be something the user started, with consent and a visible or audible indicator. Opening the mic on a timer (ambient listening, "shake or hum to search") without a clear opt-in looks like covert surveillance.
- **Verify.** Read the file: what starts the timer, how long the sensor stays open, is there an opt-in setting and an on-screen indicator, does the purpose string mention it.
- **Fix.** Make it opt-in from a settings toggle that explains it, show an indicator while listening, stop when the screen is not visible, mention it in the purpose string and the review notes. If it is not essential, remove it.

### X-RECORDING: 2.5.14
- **Rule.** Explicit consent and a clear visual or audible indicator while recording audio, video or the screen.

### X-MARKETING-PUSH: 4.5.4, 4.5.3
- **Rule.** Push must not be required for the app to work and must not carry sensitive personal data. Marketing push needs explicit opt-in and an in-app way to opt out. Live Activities and push may not be used to spam.

### IOS-EXPORT-COMPLIANCE
- Set `ITSAppUsesNonExemptEncryption` to `false` if the app only uses HTTPS and OS crypto, so uploads skip the manual question.

---

## Beyond the scanner (always list under Manual checks if relevant)

- **4.3 spam.** Is this app one of several near-identical apps from the same codebase or account (white-label, templated)? Is the category saturated? What makes it different?
- **2.1 review access.** Demo account in the review notes, backend live, any region or institution lock explained. New features described specifically (2.3.1(a)).
- **2.3 metadata.** Screenshots show the real app, name ≤ 30 characters, no prices or other platforms in the name, keywords not stuffed. 2.3.14 creative assets. iPhone Duo screenshots from April 2027.
- **Age rating.** Questionnaire answered on the 2026 scale, Shared Location and Dating answered by 2027-01-12.
- **App Privacy label** matches the SDK list in `facts.sdk_categories` (ads → identifiers and usage data, crash reporting → diagnostics, AI → user content).
- **Regulated industries** (banking, crypto exchanges and wallets, healthcare, gambling, VPN, air travel) are submitted by an organization, not an individual (5.1.1(ix), 3.1.5). Crypto: no on-device mining, no crypto rewards for tasks. Loans: APR ≤ 36% including fees, no full repayment in ≤ 60 days. Gambling and contests: licence, geo-restriction, official rules saying Apple is not a sponsor (5.3). Brazil fixed-odds betting needs an SPA licence.
- **Medical device declaration** for Health & Fitness and Medical apps in the EU, UK and US.
- **4.2.3(ii)** large downloads on first launch (ML models, asset packs) disclose the size and ask first.
- **4.7** mini apps, mini games, chatbots, emulators: content within the app's rating, filtering, report and block, per-instance consent, age restriction from verified or declared age.
- **4.10** no charging for built-in capabilities (push, camera, iCloud storage).
- **DPLA** accepted by the Account Holder (new terms 2026-10-13), or submissions are blocked.
- **Group purchases.** Auto-renewable subscriptions can be bought for multiple seats by organisations (on by default since October 2026). Make sure entitlement logic does not tie access to the account that paid.
- **Accessibility Nutrition Labels** are voluntary today. Only claim what was tested.
