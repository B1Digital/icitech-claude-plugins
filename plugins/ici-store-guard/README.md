# ici-store-guard

Uygulamayı Apple App Store ve Google Play'e göndermeden önce red sebeplerini yakalayan skill. Flutter odaklı, native ve diğer çapraz platform projelerde de çalışır.

Apple'ın 2025 şeffaflık raporuna göre retlerin yaklaşık üçte ikisi Guideline 2 (Performance: çökme, eksik içerik, test edilemeyen akış) kaynaklı. Bunları sadece kod taraması yakalamaz. Bu yüzden skill kodu, derlenmiş paketi ve çalışan uygulamayı birlikte denetler.

## Ne yapar

| Aşama | Ne kontrol eder |
|---|---|
| 1. Tarayıcı | [store-compliance](https://github.com/motivexintelligence/store-compliance-skill): SDK'lar, izinler, targetSdk, Billing, privacy manifest (2026 kuralları) |
| 2. Paralel denetim | [appstore-review / playstore-review](https://github.com/devsemih/appstore-review-skill) ve Google'ın resmi [play-policy-insights](https://github.com/android/skills/tree/main/play/play-policy-insights) aracı |
| 2b. Paket ve görseller | IPA/AAB içindeki Info.plist, entitlement, privacy manifest, ikon, ad ID'leri; mağaza ekran görüntüleri gerçek fiyat/arayüzü gösteriyor mu, dil uyumu |
| 3. Birleştirme | Tekrarları ayıklar, her bulguyu `dosya:satır` okuyarak doğrular |
| 4. Runtime | iPad simülatöründe temiz kurulum, ATT/izinler, her sekme, mağaza, geri yükleme, gizlilik linki, dark mode |
| 5. Rapor | Tek dosya: **GO / NO-GO**, BLOCK / RISK / ÖNERİ / MANUEL, konsol kontrol listesi, App Review Notes taslağı |

Denetlenen repoya hiçbir şey yazmaz. Kod değişikliği sadece istenirse yapılır.

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install ici-store-guard@icitech
```

Gereken: Python 3. iOS runtime testi için Xcode simülatörü, Android paket kontrolü için tercihen `bundletool`.

## Kullanım

Claude Code'a şunlardan birini deyin:
- "mağazaya göndermeden kontrol et"
- "bu uygulama reddedilir mi"
- `/ici-store-guard`

Argümanlar:
- `[yol]`: denetlenecek uygulama repo'su
- `--ios` / `--android`: tek mağazayla sınırla
- `--no-runtime`: simülatör testini atla
- `--quick`: yaklaşık 2 dakikalık hızlı tarama
- `--out <klasör>`: raporun yazılacağı klasör

Rapor varsayılan olarak `~/store-guard-reports/<uygulama>/` altına yazılır. Ret geldikten sonra Resolution Center yanıtı için `app-rejection-recovery` skill'i kullanılır.

## İçindekiler ve lisanslar

`skills/ici-store-guard/vendor/` klasörü üç açık kaynak denetçinin incelenmiş kopyalarını içerir. Kaynak commit'ler ve lisanslar (MIT, MIT, Apache-2.0) `vendor/VENDOR.md` dosyasında yazılı. Değerlendirilip eklenmeyen adaylar ve gerekçeleri de aynı dosyada. Vendored scriptler yalnızca Python stdlib kullanır. Dışarıya tek istek, Google aracının herkese açık Play sayfasını okumasıdır.
