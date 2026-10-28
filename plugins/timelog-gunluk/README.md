# timelog-gunluk

Her akşam o günün zaman girişi planını hazırlar ve sana Slack'te kendi DM'inden gönderir. Sen mesajın altına "onay" ya da düzeltmeni yazarsın, giriş TimeLog'a yapılır. Onay vermeden hiçbir şey girilmez.

- **23:30**: o günün planı ve varsa soruları (ör. "15:00–17:00 arası ne yaptın?") DM'ine gelir. Önce bekleyen günlerdeki cevapların işlenir.
- **09:00**: yalnız bekleyen günlerdeki cevapların işlenir.
- Cevabını ne zaman yazarsan yaz, bir sonraki çalışmada işlenir.

Plan şu kaynaklardan çıkar: git commit'lerin (kod yazıyorsan), Google Takvim toplantıların, gönderdiğin mailler. Proje eşleşmeleri ve açıklama üslubu senin kendi kurallar dosyanda durur; bu repoda kişiye ya da müşteriye ait bilgi yoktur.

## Gereksinim

- macOS ve Claude Code (claude.ai hesabıyla giriş)
- TimeLog bağlantısı (kurulum bilgisi ekip yöneticisinde)
- claude.ai'de Slack connector'ı; isteğe bağlı Gmail ve Google Takvim connector'ları

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install timelog-gunluk@icitech
/timelog-gunluk:kur
```

Kurulum eksik bağlantıları tek tek gösterir ve ayarlarını sorar.

## Komutlar

- `/timelog-gunluk:kur` — kur · `durum` — ne durumda · `kaldir` — kaldır
- `/timelog-gunluk:gunluk gun 2026-01-05 2026-01-09` — geçmiş günlerin planını gönder
