---
name: kur
description: timelog-gunluk kurulumu — bağlantıları kontrol eder, eksikleri adım adım bağlatır, kişisel ayarları sorar, her akşam/sabah çalışmayı (macOS launchd) kurar. Argüman: (boş) kur | durum | kaldir
---

# timelog-gunluk kurulumu

Kullanıcı teknik olmayabilir (ör. PM). Her adımı kısa, sade Türkçe anlat; bir seferde tek şey iste. Bir adım başarısızsa nedenini söyle, sonraki adıma geçme.

Kişisel her şey `~/.timelog-gunluk/` altına yazılır (`~/.claude/` altı Claude Code için hassas klasördür, gece çalışması oraya yazamaz). Plugin klasörüne hiçbir şey yazma.

## kur

### 1. Bağlantılar

Her birini ucuz bir çağrıyla dene:

| Bağlantı | Deneme | Yoksa |
|---|---|---|
| TimeLog | `mcp__timelog__get_me` | "TimeLog bağlantısı kurulu değil. Kurulum bilgisi için ekip yöneticine başvur." Adres, token ya da kaynak yeri **yazma**. Bu adım tamamlanmadan devam etme. |
| Slack | `slack_read_user_profile` (kendi profili) | Aşağıdaki connector tarifi |
| Gmail | `search_threads` `newer_than:1d`, pageSize 1 | Connector tarifi (isteğe bağlı; yoksa mail taranmaz) |
| Google Takvim | `list_calendars` | Connector tarifi (isteğe bağlı) |

Araç listede hiç yoksa `ToolSearch` ile ara; bağlantı yeni kurulduysa yüklenmesi birkaç saniye sürebilir.

**Connector tarifi** (Slack, Gmail, Takvim için aynı):
1. Tarayıcıda claude.ai'yi aç → sol altta adın → **Ayarlar** → **Connectors**.
2. İlgili servisi bul → **Connect** → açılan pencerede iş hesabınla izin ver.
3. Claude Code'a dön, `/mcp` yaz ve bağlantının göründüğünü kontrol et (görünmezse Claude Code'u kapatıp aç).
Kullanıcı "tamam" deyince aynı denemeyi tekrarla.

Claude Code'un claude.ai hesabıyla açılmış olması gerekir; API anahtarıyla açılmışsa connector'lar görünmez. Ortamda `ANTHROPIC_API_KEY` tanımlıysa kullanıcıya söyle: etkileşimli oturumu etkileyebilir; gece çalışması bunu zaten kaldırır.

### 2. Kişisel ayarlar

Sırayla sor, varsayılanı öner:

- **Slack kullanıcı id'si:** Slack profilinden al, sorma.
- **Git yazar adları:** `git config --global user.name` ve `user.email` öner. Kullanıcı kod yazmıyorsa boş bırak.
- **Repo klasörleri:** ev dizininde `.git` içeren klasörlerin bulunduğu kökleri öner (ör. `~/projects`). Kod yazmıyorsa boş.
- **Kurallar dosyası (`rules_file`):** müşteri/proje/aktivite eşleşmeleri ve açıklama örnekleri. Kullanıcının hâlihazırda bir TimeLog skill'i varsa (ör. `~/.claude/skills/timelog/SKILL.md`) onu kullan. Yoksa `~/.timelog-gunluk/kurallar.md`'yi aşağıdaki şablonla oluştur ve kullanıcıyla ilk 2–3 eşleşmeyi doldur (`search_projects` / `list_activities` ile id'leri doğrulayarak).
- **Günlük saat:** varsayılan 8.

Şablon (`kurallar.md`):

```markdown
# TimeLog kurallarım

## Eşleşmeler
| İş / repo | Müşteri | Proje (id) | Aktivite (id) |
|---|---|---|---|

## Açıklama üslubu
Açıklamalar müşterinin faturada okuyacağı sade cümlelerdir; teknik terim yazılmaz.
```

`config.json`'u yaz: `slack_user_id`, `dm_channel_id: ""`, `git_authors`, `repo_roots`, `rules_file`, `day_hours`, `skip_dates: []`. `state.json` yoksa `{"days": {}}`.

### 3. Zamanlama (macOS)

1. Plugin'in `bin/run.sh` dosyasını `~/.timelog-gunluk/run.sh`'ye kopyala, `chmod +x`. (Plugin güncellenince yol değişir; kopya sabit kalır. Güncellemeden sonra kurulumu tekrar çalıştırmak kopyayı yeniler.)
2. `~/Library/LaunchAgents/com.icitech.timelog-gunluk.plist` yaz: `ProgramArguments` = `/bin/bash` + kopya `run.sh`; `StartCalendarInterval` iki giriş: 23:30 ve 09:00 (kullanıcı başka saat isterse onu); `StandardOutPath`/`StandardErrorPath` = `~/.timelog-gunluk/logs/launchd.log`.
3. `launchctl bootout gui/$(id -u)/com.icitech.timelog-gunluk 2>/dev/null; launchctl bootstrap gui/$(id -u) <plist>`.
4. `~/.timelog-gunluk/run.sh test` çalıştır, en yeni log dosyasını oku. Dört bağlantı da çalışıyorsa kurulum tamam.

Mac o saatte uykudaysa iş uyanınca çalışır; kapalıysa o çalışma atlanır, bir sonraki çalışma bekleyenleri yine işler.

### 4. Kullanıcıya özet

Ne kurulduğunu, mesajın ne zaman geleceğini (her akşam, kendi Slack DM'ine; bildirim gelmez, kendin bakarsın), cevabın mesajın thread'ine yazılacağını ve geçmiş günler için `/timelog-gunluk:gunluk gun 2026-01-05 2026-01-09` kullanılabileceğini söyle.

## durum

`config.json` özeti, `launchctl print gui/$(id -u)/com.icitech.timelog-gunluk` sonucu (yüklü mü), `state.json`'da onay bekleyen günler, en son log dosyasının son satırları.

## kaldir

`launchctl bootout ...`, plist'i sil. `~/.timelog-gunluk/` klasörünü silmeden önce sor (içinde kurallar ve geçmiş durum var).
