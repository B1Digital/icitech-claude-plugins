---
name: ici-internal-documents
description: >-
  Generate professional icitech-branded internal technical documents as polished
  PDFs, always written in Turkish (plain-language rules adapted from
  simpleenglish / ASD-STE100), matching the icitech corporate template — a dark
  indigo gradient splash/cover page plus clean content pages with numbered
  section badges, rounded info boxes, dark code blocks, colored callouts,
  before/after example cards, data tables and Graphviz flow diagrams. Use whenever the user asks for an
  "ici" / "icitech" internal document, kılavuz, el kitabı, teknik doküman,
  runbook, guide, handbook, cheat-sheet, or a branded PDF report, OR references
  the TimeLog-MCP-Kurulum template style. Handles multi-page layout, embedded
  Turkish-capable fonts, and matching header/footer. Reuses a ready-made
  reportlab engine (assets/ici_doc.py); the author only writes the content story.
---

# icitech İç Doküman Motoru (PDF)

Bu skill, icitech kurumsal şablonuna (koyu indigo splash + numaralı bölümler,
yuvarlak kutular, koyu kod blokları, uyarı kutuları, before/after kartları,
veri tabloları) uygun profesyonel PDF dokümanlar üretir. Türkçe karakterler
gömülü fontlarla düzgün render edilir.

## Nasıl çalışır

Motor `assets/ici_doc.py` içinde hazır. Sen sadece **story** (içerik akışı)
yazar ve `render(...)` çağırırsın. Splash sayfası, **İçindekiler sayfası**,
header/footer, sayfa numarası, PDF yer imleri otomatik.

Tam ve çalışan örnek: **`assets/example_postgres_handbook.py`** — bunu şablon
olarak kopyalayıp içeriği değiştirmek en hızlı yoldur.

## Adımlar

1. **Kurulum (gerekiyorsa).** reportlab kurulu olmalı. İzole tut:
   ```bash
   python3 -m venv /tmp/icidoc_venv && /tmp/icidoc_venv/bin/pip install -q reportlab
   ```
   Render için PNG önizleme istiyorsan `pdftoppm` (poppler) yeterli; genelde macOS'ta `brew` ile gelir.

2. **İçerik dosyası yaz.** `example_postgres_handbook.py`'yi kopyala, story'yi
   (`e = [...]`) kendi bölümlerinle doldur, sondaki `render(...)` meta bilgisini
   (başlık, badge, splash notu, footer) güncelle. `sys.path.insert` satırını
   koru ki `ici_doc` import edilebilsin — ya da `ici_doc.py`'yi içerik
   dosyasının yanına kopyala.

3. **Üret.**
   ```bash
   /tmp/icidoc_venv/bin/python icerik_dosyasi.py cikti.pdf
   ```

4. **GÖRSEL DOĞRULA (zorunlu).** PDF'i asla görmeden teslim etme. Her sayfayı
   PNG'ye çevirip Read tool ile bak — taşma, kutu (□) çıkan karakter, hizalama
   hatası, kesilen tablo var mı kontrol et, düzelt:
   ```bash
   pdftoppm -png -r 85 cikti.pdf sayfa && ls sayfa-*.png
   ```
   Sonra her `sayfa-N.png`'yi Read ile incele.

5. **Teslim.** Kullanıcı Downloads'a istediyse oraya kopyala; yoksa scratchpad
   yeterli. Nihai konumu SendUserFile ile ilet.

## Dil: çıktı her zaman Türkçe

Bu skill'in ürettiği her doküman **Türkçe** yazılır. Kullanıcı İngilizce bir yazım kuralı
(ör. simpleenglish, ASD-STE100) verse bile o kuralın *ilkeleri* Türkçeye uyarlanır, dil Türkçe kalır.
Kod, komut, tablo/alan adı, ürün adı ve hata metni olduğu gibi kalır. `toc_title` varsayılanı `İçindekiler`.

## Sade yazım (simpleenglish / ASD-STE100'den Türkçeye uyarlandı)

Kaynak: https://github.com/aminblg/simpleenglish. Amaç: alan dışından zeki bir okur metni bir okumada anlasın.

1. **Paragrafı sınıfla.** Yapılacak iş anlatan metin (prosedür): emir kipi, cümle başına en çok ~20 kelime,
   cümle başına tek iş. Açıklayıcı metin: geniş/geçmiş zaman, cümle başına en çok ~25 kelime, paragraf başına
   tek konu, en çok altı cümle.
2. **Koda ve gerçeğe dokunma.** Kod, alan adı, komut, dosya yolu, hata metni, sayı değişmez. Kaynakta sayı
   ya da neden yoksa uydurma.
3. **Önce koşul, sonra komut:** "Derleme kırılırsa logu oku."
4. **Etken çatı, özneyi söyle:** "Kutu 2 bacağa yazar." ("yazılır" yerine). "-erek, -ip" ile uzayan zincir
   cümleleri böl.
5. **Kesin kipler:** "yapar / yapmalı / yapabilir". "Olabilir, belki, muhtemelen, gerekebilir" yalnız gerçek
   belirsizlikte; belirsizliğin nedenini yaz.
6. **Noktalı virgül ve uzun çizgi (—) yok.** İki cümle yaz ya da ilişkiyi adlandır ("çünkü", "ama", "örneğin").
7. **Bir kavram, tek kelime.** Belge boyunca aynı terimi kullan (ör. hep "bacak", bir yerde "etap" değil;
   hep "kontrol et", bir yerde "doğrula/teyit et" değil). Üçten uzun isim zincirlerini edatla böl.
8. **Terimi ilk kullanımda tanımla**, on kelimeden kısa: "idempotent (iki kez çalışsa da aynı sonucu verir)".
   Ürün ve standart adlarını (RabbitMQ, ClickHouse, SQL Server) tanımlama.
9. **Önemini değil gerçeği yaz.** "Kritik, güçlü, kapsamlı, sorunsuz, kolayca, sadece" gibi bilgi taşımayan
   kelimeleri sil. "Sonuç olarak" ile bitirme.
10. **Biçim yapı taşısın.** Vurgu için kalın kullanma; dikey liste yalnız üç ve daha fazla paralel öğe için.
11. **Uyarıda önce komut ya da koşul, sonra risk:** "Bunu canlıda çalıştırma. Komut satır siler."

Teslimden önce kendi kontrolün: en uzun üç cümlenin kelimesini say, `—` ve `;` ara, aynı kavram için iki
farklı kelime kullandın mı bak.

## Görseller (akış şeması, infografik)

Akışları kutu-ok şemasıyla göster. En hızlı yol Graphviz (`/opt/homebrew/bin/dot`):
`dot -Tpng -Gdpi=200 akis.dot -o akis.png`, sonra `figure('akis.png', 'Şekil 1: ...')`.
Şemada marka renklerini kullan (indigo `#4f46e5`, lacivert `#1b1b4b`, açık gri kutu `#f3f4f8`),
yazı tipi `Arial`. Türkçe karakterler Graphviz'de UTF-8 ile sorunsuz çıkar.

## Motorun sunduğu yapı taşları (`from ici_doc import *`)

| Fonksiyon | Ne üretir |
|---|---|
| `section(num, 'Başlık')` | İndigo numaralı rozet + bölüm başlığı. **İçindekiler'e otomatik girer** |
| `sub('1.1 · Alt başlık')` | Alt başlık (`st_h3`). İçindekiler'de bir önceki bölümün altında girintili görünür |
| `Paragraph(html, st_body)` | Normal metin (`st_body`, `st_lead`, `st_muted`, `st_h3` stilleri) |
| `box([...])` | Açık gri yuvarlak bilgi kutusu |
| `codeblock([satır,...])` | Koyu monospace kod bloğu (Türkçe yorum güvenli) |
| `callout(html, 'warn'/'good'/'info')` | Renkli sol-kenarlı uyarı kutusu |
| `beforeafter(başlık, önce, sonra, not)` | Kırmızı ✕ önce / yeşil ✔ sonra örnek kartı |
| `bullets([...])` | İndigo madde işaretli liste |
| `checklist([...])` | ☐ kutucuklu kontrol listesi |
| `datatable(header, rows, widths)` | Lacivert başlıklı, zebra desenli veri tablosu (widths = oran listesi, toplam ~1.0). Hücreler string ya da Paragraph olabilir |
| `labelrow(label, html, color=None)` | Renkli etiket çipi + metin. Hikâye/vaka adımları için: `BELİRTİ` (kırmızı), `TEŞHİS` (indigo), `DÜŞÜNCE` (mor), `AKSİYON` (mavi), `SONUÇ` (yeşil), `DERS` (turuncu) renkleri otomatik |
| `story_case(code, title)` | Vaka başlığı: küçük indigo kod + başlık, ince alt çizgi |
| `ic(char, color=None)` | Monokrom simge (✓ ✕ ☐ ▲ ◉) ArialUni'den; ⚠ → ▲, ℹ → ◉ otomatik çevrilir (glif yok). Emoji yerine bunu kullan |
| `figure(yol, caption=None, width=1.0)` | PNG/JPG görsel (ör. Graphviz akış şeması), en-boy korunur, altta soluk açıklama |
| `sp(h)` | Dikey boşluk |

Renk sabitleri: `INDIGO`, `NAVY`, `BLUE`, `PURPLE`, `GOOD`, `BAD`, `MUTED`, `INK`, `WHITE`, `HexColor('#...')`.

Kod içi tekil monospace için: `<font face="MonoTR">metin</font>`.
`<b>`, `<i>` ve `&lt; &gt; &amp;` HTML kaçışları Paragraph içinde çalışır.
Renkler ve stiller `ici_doc.py` başında (palette + `st_*`).

## İçindekiler (otomatik, kapaktan sonra)

`render()` varsayılan olarak (`toc=True`) kapaktan hemen sonra ayrı bir **İçindekiler** sayfası koyar:
her `section()` indigo numara rozeti + kalın başlık + sağda sayfa numarası; her `sub()` girintili, soluk.
Satırlar tıklanınca ilgili sayfaya gider; PDF okuyucunun yan panelinde aynı yapı yer imi (outline) olarak çıkar.
Sayfa numaraları için belge birkaç kez derlenir (otomatik; numaralar footer'daki numarayla aynıdır).

- **Elle İçindekiler tablosu yazma**: motor üretir. Başlığı `toc_title='Contents'` ile değiştir, istemezsen `toc=False`.
- Alt başlıkları İçindekiler'de görmek istiyorsan `Paragraph(..., st_h3)` yerine `sub(...)` kullan.
- `section()` numarası metin de olabilir (`section('Ek', 'Kod')`); rozet genişler.

## `render()` parametreleri (splash + header/footer)

```python
render('cikti.pdf',
    badge='ŞİRKET İÇİ TEKNİK KILAVUZ',      # splash üst rozeti
    title='Ana Başlık',                      # splash büyük başlık
    subtitle='Alt Başlık',
    subline='PostgreSQL · ek bilgi',         # opsiyonel küçük satır (teknoloji notu vb.)
    desc_lines=['1. satır', '2. satır'],     # splash açıklama paragrafı (satır satır)
    version='v1.0',
    meta_line='Temmuz 2026 · Yazılım Ekibi · Hazırlayan: ...',
    header_title='İç sayfa üst-sağ başlık',
    header_sub='Alt · v1.0',
    footer_left='sol alt tagline',
    story=e,
    toc=True,                                # kapaktan sonra otomatik İçindekiler (varsayılan)
    toc_title='İçindekiler')
```

## Şablon & marka kuralları

- **Marka:** logo hep `icitech` (küçük harf). Splash koyu indigo gradient,
  içerik sayfaları beyaz. Ana aksan indigo `#4f46e5`, başlıklar lacivert `#1b1b4b`.
- **Splash:** logo sol-üst, badge → başlık → subtitle → subline → açıklama →
  versiyon pill + meta, altta ince çizgi + "Shape your digital future with us." /
  "www.icitech.com.tr".
- **Ton:** kısa ama gerektiği kadar açıklayıcı; kopyala-çalıştır komutlar;
  gerçek "önce → sonra" örnekleri (`beforeafter`). Referans model: TimeLog-MCP
  kurulum kılavuzu ve `example_postgres_handbook.py`.
- **Türkçe:** metinler her zaman Türkçe (bkz. "Dil"). Fontlar Türkçe karakter
  destekli (macOS Arial; yoksa DejaVu/Vera'ya düşer).

## Hikâyeleştirme (vaka kalıbı)

Teknik vakaları anlatırken `story_case` + `labelrow` kalıbını kullan. Her vaka
şu iskeleti izler ve okunması akıcı olur:

```python
e += [KeepTogether([story_case('tablo_adi', 'Kısa vaka başlığı'), sp(5),
    labelrow('BELİRTİ', 'Ne gördük (log satırı, süre).'), sp(3),
    labelrow('TEŞHİS',  'EXPLAIN ne dedi.'), sp(3),
    labelrow('DÜŞÜNCE', 'Neden, nasıl karar verdik.'), sp(3),
    labelrow('AKSİYON', 'Ne yaptık.'), sp(3),
    codeblock(["CREATE INDEX ..."]), sp(4),
    labelrow('SONUÇ',   '<b>441 ms → 0.22 ms.</b> Ölçülen kazanç.'),
])]
```

Önce/sonra kıyasları için `beforeafter(...)` kartını ya da metinde `→` okunu
kullan. Em-dash (`—`) kullanma.

## Prose kalitesi — stop-slop

Metni yazınca `stop-slop` skill'inin kurallarını uygula (kuruluysa
`references/phrases.md` ve `structures.md`). Türkçe metne uyan başlıcalar:

- **Em-dash yok.** `—` yerine `:` (açıklama), `,` (ara söz) ya da `.` (yeni cümle).
  Bölüm başlıklarında `:` kullan (`İndeks İş Akışı: 6 Adım`).
- **Throat-clearing kes.** "Ama dürüst olalım:", "Aslında şu ki", "Gerçekten
  yaşadık:" gibi girişleri sil, doğrudan içeriğe geç.
- **Filler at.** Boşta duran "aslında, gerçekten, sadece, tamamen"; hatalı `, ve`
  bağlacı; anlam katmayan pekiştireçler.
- **Aktif çatı, spesifik ol.** "Süre düştü" yerine "441 ms'den 0.22 ms'ye indi".
- **Ritmi değiştir.** Art arda aynı uzunlukta cümle kurma; her paragrafı aynı
  vurucu tek cümleyle bitirme.

Teknik doğruluğu ve bilinçli gruplamaları (ör. "üç altın kural") bozma —
stop-slop prose sloppuğunu temizler, teknik içeriği değil.

## Emoji uyarısı

Gömülü Arial renkli emoji (⚠️ ✅ ❌) içermez — bunlar kutu (□) çıkar. Monokrom
simge gerekince `ic('✔','#15803d')` gibi `ic()` yardımcısını kullan (ArialUni'den
✓ ✕ ☐ ▲ ◉ basar; ⚠ ve ℹ glifi yok, ic() bunları ▲ ve ◉ yapar). `callout` ve `beforeafter` bunu zaten yapar.

## Not: veritabanı projeye göre değişir

icitech'in kendi ürünleri **PostgreSQL** kullanır (uygulama: Go, `database/sql`); orada örnekleri
PostgreSQL'e göre ver. Başka projede (ör. SQL Server + ClickHouse kullanan bir .NET projesi) o projenin
veritabanını kullan. Hangisi olduğunu splash `subline`'ında belirt.
