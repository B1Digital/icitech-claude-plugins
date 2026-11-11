# ici-game-ads

Mobil oyunlar için Google Ads uygulama kampanyası reklam öğeleri üreten skill: sinematik videolar ve yazısız reklam görselleri. Oyunun kendi görsellerinden yola çıkar, yapay zekâ görsel ve video modellerini kullanır.

## Ne üretir

| Çıktı | Ayrıntı |
|---|---|
| Videolar | Dikey (9:16), yatay (16:9) ve kare (1:1). 10 saniyelik sahne ve 2,5 saniyelik kapanış kartı (ikon, oyun adı, slogan, "PLAY FREE"). 1080p, oyunun kendi müziği ve ses efektleriyle |
| Görseller | 1200×628, 1200×1200 ve 1200×1500. Yazısız |

## Nasıl çalışır

| Adım | Ne olur |
|---|---|
| 1. Oyunu tanıma | Ekran görüntüleri, maskot, ikon, font ve seslerden oyunun mekaniği çıkarılır |
| 2. Plan | Oyun deposuna bir `plan.json` yazılır: konseptler, promptlar, referans görseller |
| 3. Kareler | Her video için oyunun gerçek görsellerinden başlangıç ve bitiş karesi üretilir |
| 4. Video | İki kare arasındaki hareket görselden videoya modeliyle üretilir |
| 5. Montaj | Kapanış kartı, müzik ve efektler eklenir |
| 6. Kontrol | Her video ve görsel kare kare incelenir; hatalı olan yeniden üretilir |

Kurallar skill'in içinde yazılıdır: oyunda olmayan bir şey gösterilmez, görsellerde yazı olmaz, video 10 saniyeden kısa olmaz, kapanış kartında "Download" ya da "Install" yazmaz.

Yüklemeyi skill yapmaz. Üretilen dosyaları Google Ads öğe kitaplığına siz yüklersiniz; skill adımları söyler.

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install ici-game-ads@icitech
```

Gerekenler:

- Python 3.9 veya üstü
- `ffmpeg` ve `ffprobe`
- Google Chrome ya da Chromium (kapanış kartını çizer)
- Bir [fal.ai](https://fal.ai) API anahtarı

## Anahtarlar

Anahtarlar depoya ya da plan dosyasına yazılmaz. Bilgisayarınızda şu dosyada durur:

```
~/.config/ici-game-ads/keys.env
```

İçeriği:

```
FAL_KEY=...
CODEFAST_KEY=...
```

`CODEFAST_KEY` isteğe bağlıdır; görselleri GPT Image üzerinden üretmek isterseniz kullanılır. Dosya iznini `chmod 600` yapın. Anahtarları ortam değişkeni olarak da verebilirsiniz.

Kurulumu denetlemek için:

```
python3 <skill klasörü>/scripts/gameads.py check
```

Bu komut araçların ve anahtarların var olup olmadığını söyler, anahtar değerlerini göstermez.

## Kullanım

Oyunun deposunda Claude Code'a şunlardan birini deyin:

- "bu oyun için Google Ads reklam videoları üret"
- "reklam görselleri lazım"
- `/ici-game-ads`

Skill önce konseptleri bir tabloyla gösterir, onayınızdan sonra üretir.

## Maliyet

Üretim ücretlidir ve sağlayıcının güncel fiyatına bağlıdır. Bir örnek üretimde 10 saniyelik bir video yaklaşık 0,30 dolar tuttu; altı video ve dokuz görsellik bir set birkaç doları geçmedi. Yeniden üretimler buna dahil değildir.
