---
name: gunluk
description: Günlük TimeLog akışı — günün zaman girişi planını kullanıcının kendi Slack DM'ine atar, thread'deki cevabı okur, onay gelince TimeLog'a girer. launchd'den `run.sh` ile çalışır; elle de çağrılabilir. Argüman: aksam | sabah | test | gun YYYY-MM-DD [YYYY-MM-DD]
---

# Günlük TimeLog akışı

Bu skill çoğunlukla kimse başında yokken (`claude -p`) çalışır. Kullanıcıya soru soramazsın; sorularını Slack mesajına yaz.

## Dosyalar (hepsi `~/.claude/timelog-gunluk/` altında, repoda değil)

- `config.json` — kişisel ayarlar (`/timelog-gunluk:kur` oluşturur):
  `slack_user_id`, `dm_channel_id` (ilk gönderimden sonra doldur), `git_authors` (dizi), `repo_roots` (dizi; boş olabilir), `rules_file` (eşleşme tabloları ve açıklama kuralları), `day_hours` (varsayılan 8), `skip_dates` (dizi).
- `state.json` — gün gün durum: `{"days": {"YYYY-MM-DD": {"status", "thread_ts", "last_reply_ts", "plan": [...], "questions": [...], "timesheet_ids": [...]}}}`.
  `status`: `sent` (onay bekliyor) · `entered` (girildi) · `skipped` (kullanıcı "boş kalsın" dedi).
  `plan` satırı: `{"start":"HH:MM","end":"HH:MM","projectId":n,"activityId":n,"project":"ad","activity":"ad","description":"...","source":"commit|takvim|mail|slack|kullanıcı"}`.
- `config.json` ya da `state.json` yoksa, ya da `rules_file` okunamıyorsa: hiçbir şey gönderme, çıktıya nedenini yaz ve dur.

**Önce `rules_file`'ı oku.** Müşteri, proje ve aktivite eşleşmeleri ve açıklama üslubu oradadır. Bu skill'deki genel kurallarla çelişirse `rules_file` geçerlidir. Proje/aktivite id'si uydurma; `search_projects` / `list_activities` ile doğrula.

## Modlar

- `aksam`: 1) **Bekleyenleri işle**, 2) bugünü **hazırla ve gönder**.
- `sabah`: yalnız **bekleyenleri işle**.
- `gun A [B]`: A'dan B'ye (B yoksa yalnız A) her gün için **hazırla ve gönder**. Geçmiş günleri doldurmak içindir. Önce bekleyenleri işle.
- `test`: hiçbir şey göndermeden şunları dene ve sonucu yaz: `get_me`, Slack profil okuma, Gmail arama, takvim listesi, `config.json` ve `rules_file` okunabiliyor mu.

## Bekleyenleri işle

`state.json`'daki her `sent` gün için:

1. `slack_read_thread(dm_channel_id, thread_ts)`.
2. `last_reply_ts`'den sonraki, **`🤖` ile başlamayan** mesajlar kullanıcının cevabıdır (bizim mesajlarımız hep `🤖` ile başlar; ikisi de aynı hesaptan gider). Yeni cevap yoksa geç.
3. Cevabı yorumla:
   - **Onay** ("onay", "tamam", "ok", "gir", 👍 gibi) → aşağıdaki **Gir** adımı.
   - **Ekle / düzelt / sil** → planı güncelle, aynı thread'e güncel tabloyu `🤖` ile başlayarak yeniden onaya sun. Kullanıcı aynı mesajda açıkça "ekle ve gir" dediyse güncelle ve doğrudan **Gir**.
   - **Boş kalsın / girme** → `status: skipped`, thread'e kısa teyit.
   - **Soruya cevap** (ör. "o saatlerde X toplantısı") → planı güncelle, yeniden onaya sun.
   - Anlamadıysan thread'e kısa bir soru yaz.
4. `last_reply_ts`'i işlediğin son cevabın ts'i yap.

### Gir

1. `list_timesheets(begin: "<gün>T00:00:00", end: "<gün>T23:59:59")` — çakışan giriş varsa o satırı girme, thread'de belirt.
2. Her plan satırı için `log_time`. Dönen id'leri `timesheet_ids`'e yaz.
3. `status: entered`; thread'e `🤖 Girildi: N kayıt, toplam X saat.` Hata olan satırı adıyla yaz.

**Onaysız asla `log_time` çağırma.**

## Hazırla ve gönder (bir gün için)

Gün `skip_dates`'te, hafta sonunda ya da takvimdeki resmi tatilde ve hiç iz yoksa: gönderme. Durumu `entered`/`sent` olan günü yeniden gönderme.

1. **Mevcut girişler:** `list_timesheets` o gün. Gün zaten `day_hours` kadar doluysa gönderme.
2. **Commit'ler** (`repo_roots` boş değilse): her kökün altındaki git repolarında
   `git -C <repo> log --all --since="<gün> 00:00" --until="<gün> 23:59" -i --author=<her yazar> --date=format:%H:%M --pretty="%ad|%s"`.
   Merge commit'leri iş sayma. Aynı saat ve mesajla birden fazla repoda görünen commit (worktree/kopya) tek iş sayılır.
3. **Takvim:** `list_events` o gün; katıldığı, iptal olmayan toplantılar gerçek saatleriyle girer, kodlama bloğunu kaydırır.
4. **Mail:** `search_threads` `from:me after:<gün> before:<gün+1>`; müşteriye analiz, rapor, destek yanıtı gibi iş içerenler. Bülten, otomatik bildirim, kısa teşekkür sayılmaz. Tarih için gerekirse `get_thread`.
5. **Planı kur:** `rules_file`'daki eşleşmelerle proje/aktivite; açıklamalar müşterinin okuyabileceği sade Türkçe (teknik terim yok). Saatleri iz zamanlarından tahmin et; öğle arası ~1 saat; toplam `day_hours`; saatler her gün aynı kalıpta olmasın. Eşleşmeyen işi plana koyma, soru yap.
6. **Sorular:** izi olmayan boş saat aralıkları, eşleşmeyen repo/iş, emin olmadığın proje.
7. **Gönder:** `slack_send_message(channel_id: dm_channel_id ya da yoksa slack_user_id)`. İlk gönderimde dönen `channel_id`'yi `config.json`'a `dm_channel_id` olarak yaz. Mesaj biçimi:

```
🤖 *TimeLog — 12 Ekim Pazartesi* (plan, onay bekliyor)

| Saat | Proje / Aktivite | Açıklama | Kaynak |
|---|---|---|---|
| 09:20–12:40 | Proje / Aktivite | ... | commit |

Toplam: 8,0 saat

*Sorular*
1. 15:00–17:00 arasında iz yok; ne yaptın?

Cevabını bu mesajın altına yaz: "onay", ya da ekle/düzelt ("14:00–15:30 X toplantısı ekle").
```

İz hiç yoksa yine gönder: tablo yerine "Bugün için iz bulamadım. Ne yaptın? Boş kalacaksa 'boş' yaz."

8. `state.json`'a `status: sent`, `thread_ts` (gönderilen mesajın ts'i), `last_reply_ts` = `thread_ts`, `plan`, `questions`.

## Sonunda

Çıktıya tek paragraf özet yaz (log dosyasına gider): hangi günler işlendi, gönderildi, girildi, hata.
