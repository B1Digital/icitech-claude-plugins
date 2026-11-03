# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ici_doc import *

e = []

# ============================================================ GİRİŞ
# İçindekiler otomatik: render(toc=True) kapaktan sonra section()/sub() başlıklarından üretir.
e += [Paragraph('Bu Kitap Nasıl Doğdu', st_h3), sp(4)]
e += [Paragraph('Bir sabah loglarda tek bir satır belirdi: <font face="MonoTR">too many clients already</font>. '
    'Uygulama veritabanına bağlanamıyordu. O satırı çekmeye başlayınca, ardında koca bir yumak çıktı: '
    'indekssiz milyon satırlık tablolar, saatlerce kümülatif süre yiyen sorgular, kendini tekrarlayan bir view, '
    've bir avuç “yavaş görünen ama masum” sorgu. Bir günde bunları tek tek çözdük '
    've her adımda aynı birkaç kural işe yaradı.', st_lead), sp(6)]
e += [Paragraph('Bu el kitabı o günün damıtılmış hâli. Amacı: <b>lise düzeyinde birinin bile</b> bir yavaş sorguyla '
    'karşılaşınca panik yapmadan, adım adım, kopyala-çalıştır komutlarla kök nedeni bulup çözebilmesi. '
    'Teorik değil, her bölümde gerçekten yaşadığımız örnekler var: neyi kötü gördük, ne düşündük, ne yaptık, ne oldu.', st_body), sp(6)]
e += [callout('Altyapımız <b>PostgreSQL</b> (uygulama tarafı Go, <font face="MonoTR">database/sql</font>). '
    'Tüm komutlar ve örnekler PostgreSQL’e göredir.', 'info')]

# ============================================================ 0
e += [sp(14), section(0,'Altın Kural: Önce Ölç'), sp(7)]
e += [Paragraph('Bir sorgu logda yavaş göründü diye hemen indeks eklemeyin. Loglardaki süre, sorgunun '
    'veritabanında geçirdiği süre <b>değildir</b>, bağlantı bekleme + ağ gecikmesi + veri aktarımı da o rakama dahildir. '
    'Bu yüzden ilk iş her zaman aynıdır:', st_lead), sp(7)]
e += [box([
    labelrow('1', 'Sorguyu <font face="MonoTR">EXPLAIN (ANALYZE, BUFFERS)</font> ile çalıştır.', INDIGO),
    sp(3),
    labelrow('2', 'En alttaki <b>Execution time</b> satırına bak, asıl DB süresi budur.', INDIGO),
    sp(5),
    bullets([
        '<b>Yüksekse</b> (yüzlerce ms / saniyeler) → DB gerçekten yavaş. İndeks veya sorgu düzeltmesi gerekir.',
        '<b>Mikrosaniye ise</b> (0.05 ms gibi) → DB zaten hızlı. Sorun <b>bağlantı havuzu / ağ / uygulama</b> tarafındadır; indeks eklemek boşa çaba olur.',
    ]),
])]
e += [sp(6), callout('Bir gün loglarda üç ayrı sorgu “yüzlerce ms” görünüyordu. '
    'EXPLAIN çekince üçü de DB’de <b>mikrosaniye</b> sürüyordu; suç bağlantı havuzunun tıkanmasıydı. '
    'Ölçmeseydik, günü boşuna indeks kovalayarak geçirirdik.', 'good')]

# ============================================================ 1
e += [sp(14), section(1,'Bağlantı Krizi: “too many clients already”'), sp(7)]
e += [Paragraph('Her şeyin başladığı yer. Sabah 10:13, loglarda:', st_body), sp(4)]
e += [codeblock(['FATAL: sorry, too many clients already (SQLSTATE 53300)']), sp(6)]
e += [labelrow('BELİRTİ', 'Uygulama DB’ye hiç bağlanamıyor. Bu bir <b>bağlantı sayısı</b> limiti (RAM ile ilgisi yok). '
    'PostgreSQL’in kabul ettiği eşzamanlı bağlantı sayısı (<font face="MonoTR">max_connections</font>, varsayılan 100) dolmuş.'), sp(6)]

e += [Paragraph('Adım 1: Anında nefes aldır', st_h3), sp(3)]
e += [Paragraph('Kriz anında önce sistemi ayağa kaldır: restart en hızlısı, ya da boştaki (idle) bağlantıları öldür.', st_body), sp(4)]
e += [codeblock([
    "-- durum tespiti",
    "SELECT count(*) FROM pg_stat_activity;   -- kaç bağlantı açık?",
    "SHOW max_connections;                    -- limit ne?",
    "",
    "-- boştaki bağlantıları kapat (superuser gerekir)",
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity",
    "WHERE state = 'idle' AND pid <> pg_backend_pid();",
]), sp(5)]
e += [callout('SQL bile çalışmıyorsa (tüm slotlar dolu) superuser rezerve slotuyla gir '
    '(<font face="MonoTR">superuser_reserved_connections</font>, varsayılan 3) ya da servisi restart et: '
    '<font face="MonoTR">sudo systemctl restart postgresql</font>.', 'warn')]

e += [sp(8), Paragraph('Adım 2: Kim dolduruyor? Dedektiflik', st_h3), sp(3)]
e += [labelrow('TEŞHİS', 'Restart geçici çözer ama sebep durur. Kaç ayrı kaynağın bağlandığına baktık:'), sp(4)]
e += [codeblock([
    "SELECT client_addr, count(*) FROM pg_stat_activity",
    "WHERE datname = 'app_db'",
    "GROUP BY client_addr ORDER BY 2 DESC;",
]), sp(5)]
e += [Paragraph('İlk çekimde <b>5</b> farklı IP çıktı: 3 DigitalOcean uygulama sunucusu, birkaç docker container, '
    'bir de Türk ISP’sinden bir adres, birinin <b>dev laptop’u</b>, doğrudan production DB’ye bağlı. Az sonra tekrar '
    'baktık: <b>7</b> olmuştu.', st_body), sp(5)]
e += [labelrow('DÜŞÜNCE', 'Kaynak sayısı <b>sabit değil, büyüyordu.</b> Uygulama koduna baktık '
    '(<font face="MonoTR">init.go</font>), havuz ayarı vardı ama değeri: <font face="MonoTR">SetMaxOpenConns(80)</font>. '
    'Tek instance için 80 sınırdaydı; ama 7 kaynak × 80 = 560, yani 100’lük tavanı katlıyordu.', PURPLE), sp(6)]

e += [Paragraph('Adım 3: Altın formül ve kalıcı çözüm', st_h3), sp(3)]
e += [Paragraph('Bağlantıyı iki taraf birlikte belirler: DB tavanı (<font face="MonoTR">max_connections</font>) '
    've her uygulamanın havuzu (<font face="MonoTR">MaxOpenConns</font>). Kural:', st_body), sp(5)]
e += [box([
    Paragraph('<font face="MonoTR"><b>MaxOpenConns × (uygulama_instance_sayısı) + rezerve(3)  &lt;  max_connections</b></font>', st_small),
], fill=HexColor('#eef0ff'), brd=INDIGO2)]
e += [sp(6), Paragraph('Uygulama tarafı, Go (<font face="MonoTR">database/sql</font>), DB bağlantısının kurulduğu yer:', st_body), sp(4)]
e += [codeblock([
    "db.SetMaxOpenConns(15)                  // bu app en fazla 15 bağlantı açar",
    "db.SetMaxIdleConns(5)                   // boşta en fazla 5 tut",
    "db.SetConnMaxIdleTime(2 * time.Minute)  // boştakini 2 dk sonra kapat",
    "db.SetConnMaxLifetime(5 * time.Minute)  // 5 dk'yı geçen bağlantıyı yenile",
]), sp(5)]
e += [Paragraph('DB tarafı, RAM boldaysa tavanı da yükselt (kalıcı; <font face="MonoTR">max_connections</font> restart ister):', st_body), sp(4)]
e += [codeblock([
    "ALTER SYSTEM SET max_connections = 200;  -- postgresql.auto.conf'a kalıcı yazar",
    "-- sonra: sudo systemctl restart postgresql",
]), sp(6)]
e += [beforeafter('Bağlantı krizi: çözüm',
    '7 kaynak × <font face="MonoTR">MaxOpenConns=80</font> = 560 → 100’lük tavanı anında aştı. Havuz doldu, uygulama DB’ye giremedi.',
    '<font face="MonoTR">MaxOpenConns 80→15</font> + <font face="MonoTR">max_connections 100→200</font>. Hesap: 7×15+3 = 108 &lt; 200. Kriz kapandı, bir daha tekrarlamadı.',
    'Uyarı: sadece <font face="MonoTR">max_connections</font> artırmak (havuzu sınırlamadan) semptomu erteler, çözmez; her bağlantı da birkaç MB RAM yer. Asıl ilaç havuz sınırıdır.')]
e += [sp(6), labelrow('DERS', 'Dev laptop’undan doğrudan production DB’ye bağlanmak '
    'hem kontrolsüz slot yer hem güvenlik riskidir. Kaynak listesini ara ara denetleyin.', HexColor('#b45309'))]

# ============================================================ 2
e += [sp(14), section(2,'RAM Ayarları (shared_buffers)'), sp(7)]
e += [Paragraph('“PostgreSQL çok az RAM kullanıyor” çoğu zaman <b>normaldir</b>, asıl hızını işletim sisteminin '
    'dosya cache’inden alır, kendi belleğini küçük tutar. Ama <font face="MonoTR">shared_buffers</font> aşırı düşükse '
    '(bizde <b>8 MB</b>’ydı) gerçekten sorundur.', st_body), sp(6)]
e += [Paragraph('Önce mevcut değerleri gör:', st_body), sp(3)]
e += [codeblock(['SHOW shared_buffers;   SHOW effective_cache_size;   SHOW work_mem;']), sp(6)]
e += [Paragraph('16 GB’lık, PostgreSQL’in Redis/RabbitMQ ile paylaştığı bir sunucu için makul değerler '
    '(kalıcı; <font face="MonoTR">shared_buffers</font> restart ister):', st_body), sp(4)]
e += [codeblock([
    "ALTER SYSTEM SET shared_buffers = '4GB';         -- RAM'in ~%25'i, GERÇEK ayırır",
    "ALTER SYSTEM SET effective_cache_size = '12GB';  -- sadece planner ipucu, RAM ayırmaz",
    "ALTER SYSTEM SET work_mem = '16MB';              -- DİKKAT: bağlantı BAŞINA!",
]), sp(6)]
e += [callout('<b>work_mem tuzağı:</b> bu değer her bağlantı ve her sort/hash işlemi için ayrı ayrı kullanılır. '
    '<font face="MonoTR">64MB × 200 bağlantı × birkaç sort</font> = anında GB’larca RAM ve OOM riski. 16–32 MB’ı aşmayın.', 'warn')]
e += [sp(6), beforeafter('shared_buffers',
    '<font face="MonoTR">shared_buffers = 8MB</font>, 16 GB’lık makinada komik derecede düşük; DB neredeyse hiç kendi cache’ini kullanmıyordu.',
    '<font face="MonoTR">8MB → 4GB</font>. Restart sonrası DB kendi cache’ini kullanmaya başladı.',
    '“RAM’i daha çok kullansın” tek başına bir hedef değildir. Somut, ölçülen bir yavaşlık yoksa bu ayarlara dokunmayın; çalışan şeyi kurcalamak yeni sorun üretir.')]

# ============================================================ 3
e += [sp(14), section(3,'EXPLAIN Çıktısını Okumak'), sp(7)]
e += [Paragraph('EXPLAIN çıktısı korkutucu görünür ama okuması basittir. Plan bir ağaçtır ve '
    '<b>içten dışa / aşağıdan yukarı</b> okunur: en içteki (en girintili) düğüm ilk çalışır, sonuç yukarı akar.', st_lead), sp(7)]
e += [Paragraph('En sık görülen düğümler', st_h3), sp(3)]
e += [datatable(['Düğüm','Ne yapar / ne anlama gelir'],
    [
        [Paragraph('<font face="MonoTR">Seq Scan</font>',st_tdm), Paragraph('Tüm tabloyu baştan sona okur. Büyük tabloda kırmızı bayrak, genelde indeks eksik.',st_td)],
        [Paragraph('<font face="MonoTR">Index Scan</font>',st_tdm), Paragraph('İndeksten ilgili satırları bulur, sonra tablodan (heap) çeker. İstenen.',st_td)],
        [Paragraph('<font face="MonoTR">Index Only Scan</font>',st_tdm), Paragraph('Cevap tamamen indekste; tabloya hiç gitmez. En hızlısı.',st_td)],
        [Paragraph('<font face="MonoTR">Bitmap ... Scan</font>',st_tdm), Paragraph('Çok satır eşleşince indeks + heap’i toplu okur. Genelde iyi.',st_td)],
        [Paragraph('<font face="MonoTR">Nested Loop</font>',st_tdm), Paragraph('Küçük tarafın her satırı için diğerinde arama. Küçük kümelerde ideal.',st_td)],
        [Paragraph('<font face="MonoTR">Hash Join</font>',st_tdm), Paragraph('Bir tarafı RAM’de hash’ler, diğerini tarar. Büyük eşleşmelerde iyi.',st_td)],
        [Paragraph('<font face="MonoTR">Merge / Semi Join</font>',st_tdm), Paragraph('Sıralı iki kümeyi birleştirir; <font face="MonoTR">EXISTS</font> için semi-join erken durabilir.',st_td)],
        [Paragraph('<font face="MonoTR">Sort</font>',st_tdm), Paragraph('Sıralama. Uygun indeks varsa bu adım tamamen kaybolabilir.',st_td)],
    ],
    [0.28,0.72])]
e += [sp(8), Paragraph('Bakılacak sayılar', st_h3), sp(3)]
e += [bullets([
    '<b><font face="MonoTR">actual time=...</font></b> ve en alttaki <b><font face="MonoTR">Execution time</font></b>, gerçek süre. Asıl karar bunda.',
    '<b><font face="MonoTR">Rows Removed by Filter</font></b> yüksekse → çok satır okunup atılıyor; indeks/filtre yanlış.',
    '<b><font face="MonoTR">loops=N</font></b>, düğüm N kez çalışmış. Süreyi <font face="MonoTR">actual time × loops</font> ile düşün.',
    '<b><font face="MonoTR">Buffers: shared hit=... read=...</font></b>, <font face="MonoTR">hit</font> RAM’den, <font face="MonoTR">read</font> DİSKTEN. Yüksek <font face="MonoTR">read</font> = yavaş I/O.',
    'Tahmini (<font face="MonoTR">rows=</font> maliyet) ile <b>gerçek</b> (<font face="MonoTR">actual rows</font>) çok ayrışıyorsa → istatistik eski, <font face="MonoTR">ANALYZE</font> çek.',
])]
e += [sp(6), callout('Kısayol: çıktıda <b>“Seq Scan on &lt;büyük_tablo&gt;”</b> + yüksek <b>“Rows Removed by Filter”</b> + '
    'diskten <b>read</b> görüyorsan, %90 ihtimalle filtre kolonuna indeks eksiktir.', 'info')]

# ============================================================ 4
e += [sp(14), section(4,'İndeks İş Akışı: 6 Adım'), sp(7)]
e += [Paragraph('Yavaş sorgunun DB’de gerçekten yavaş olduğunu EXPLAIN ile doğruladıktan sonra, bu altı adımı sırayla uygula.', st_lead), sp(8)]
steps = [
    ('Adım 1: Teşhis (EXPLAIN)', 'Sorguyu çalıştır, planı oku:',
     ["EXPLAIN (ANALYZE, BUFFERS)","SELECT * FROM tablo WHERE kolon = 123 ORDER BY x;"],
     '<b>Seq Scan</b> + yüksek <b>Rows Removed by Filter</b> → indeks yok, tüm tablo taranıyor. Aranan durum bu.'),
    ('Adım 2: Zaten indeks var mı?', 'Körlemesine oluşturma; belki var ama <b>yanlış kolonla</b>.',
     ["SELECT indexname, indexdef FROM pg_indexes","WHERE tablename = 'tablo';"],
     '<b>Lider kolon kuralı:</b> indeks ancak <b>ilk kolonu</b> sorguda kullanılırsa devreye girer. '
     '<font face="MonoTR">(hotel_id, asset_id)</font> indeksi, sadece <font face="MonoTR">WHERE asset_id=?</font> için ÇALIŞMAZ.'),
    ('Adım 3: Doğru indeksi oluştur', 'Canlıda <font face="MonoTR">CONCURRENTLY</font> kullan, tabloyu kilitlemez '
     '(transaction bloğunda çalışmaz, tek başına çalıştır).',
     ["CREATE INDEX CONCURRENTLY idx_tablo_kolon","  ON tablo (kolon);"],
     'İsimlendirme: <font face="MonoTR">idx_&lt;tablo&gt;_&lt;kolonlar&gt;</font>, sonradan ne işe yaradığı anlaşılsın.'),
    ('Adım 4: İndeks geçerli mi?', '<font face="MonoTR">CONCURRENTLY</font> yarıda kalırsa GEÇERSİZ (invalid) indeks bırakır:',
     ["SELECT indexrelid::regclass, indisvalid","FROM pg_index WHERE NOT indisvalid;"],
     'Boş dönmeli. Bir satır dönerse o indeksi <font face="MonoTR">DROP INDEX</font> edip Adım 3’ü tekrarla.'),
    ('Adım 5: İstatistik + doğrula', 'Planner’ın yeni indeksi görmesi için istatistikleri tazele, sonra aynı EXPLAIN’i tekrar çalıştır:',
     ["ANALYZE tablo;","EXPLAIN (ANALYZE, BUFFERS) SELECT ... ;"],
     'Beklenen: <b>Seq Scan gitti → Index Scan geldi.</b> <font face="MonoTR">Buffers</font> ve süre çöktü.'),
    ('Adım 6: Gereksiz / duplicate sil', 'Aynı kolonlarda iki indeks = boşuna disk + her yazmada çift maliyet.',
     ["-- pg_indexes'te aynı tanımlı iki indeks varsa:","DROP INDEX gereksiz_olan_indeks;"],
     'İndeks bedava değildir: her INSERT/UPDATE onu da günceller. Kullanılmayanı taşımayın.'),
]
for title,intro,code,note in steps:
    e += [KeepTogether(box([Paragraph(title,st_h3), sp(3), Paragraph(intro,st_body), sp(4), codeblock(code), sp(4), Paragraph(note,st_muted)])), sp(7)]

# ============================================================ 5, VAKALAR
e += [sp(10), section(5,'Vaka Çalışmaları: Sahadan Hikâyeler'), sp(6)]
e += [Paragraph('Her vaka aynı iskeleti izler: <b>BELİRTİ</b> (ne gördük) → <b>TEŞHİS</b> (EXPLAIN ne dedi) → '
    '<b>DÜŞÜNCE</b> (neden) → <b>AKSİYON</b> (ne yaptık) → <b>SONUÇ</b>.', st_body), sp(10)]

# 5.1 survey_summaries
e += [KeepTogether([story_case('survey_summaries', 'Yarım milyon satır, tek indeks yok'), sp(5),
    labelrow('BELİRTİ','Bir günlük rapor 5+ saniye sürüyordu: <font face="MonoTR">WHERE hotel_id=824 AND created_at BETWEEN bugün</font>, sadece 9 satır dönüyor.'), sp(3),
    labelrow('TEŞHİS','EXPLAIN: <b>Seq Scan</b>, 497.859 satır tarandı, çoğu diskten okundu (<font face="MonoTR">read=119.830</font>). Tablonun tek indeksi <font face="MonoTR">pkey</font>’di.'), sp(3),
    labelrow('AKSİYON','Filtreyi karşılayan bileşik indeks:', BLUE), sp(3),
    codeblock(["CREATE INDEX CONCURRENTLY idx_survey_summaries_hotel_created",
               "  ON survey_summaries (hotel_id, created_at);"]), sp(4),
    labelrow('SONUÇ','<b>5.354 ms → 0.19 ms</b> (~27.000 kat). Buffers 119.830 → 2. Diskten okuma tamamen bitti.', GOOD),
])]
e += [sp(11)]

# 5.2 survey_researches
e += [KeepTogether([story_case('survey_researches', 'Join’in gizli maliyeti'), sp(5),
    labelrow('BELİRTİ','4 satır için 1 saniye. Filtre çok seçiciydi (tek otel + tek profil), tuhaftı.'), sp(3),
    labelrow('TEŞHİS','EXPLAIN: <font face="MonoTR">request_headers</font> tarafı kusursuz (0.08 ms). Ama join edilen '
        '<font face="MonoTR">survey_researches</font>’te <b>Seq Scan, 951.949 satır</b>, 285 ms. <font face="MonoTR">request_id</font>’ye indeks yoktu.'), sp(3),
    labelrow('DÜŞÜNCE','Join <font face="MonoTR">sr.request_id = rh.id</font> üzerindendi. İndeks olmayınca her join için tüm survey tablosu taranıyordu.', PURPLE), sp(3),
    labelrow('AKSİYON','', BLUE),
    codeblock(["CREATE INDEX CONCURRENTLY idx_survey_researches_request_id",
               "  ON survey_researches (request_id);"]), sp(4),
    labelrow('SONUÇ','<b>441 ms → 0.22 ms</b> (~2.000 kat). Bonus: bu tabloyu <font face="MonoTR">request_id</font> ile join’leyen <b>her</b> sorgu hızlandı.', GOOD),
])]
e += [sp(11)]

# 5.3 profile_visits
e += [KeepTogether([story_case('profile_visits', 'Tek değer çok sık: partial indeks'), sp(5),
    labelrow('BELİRTİ','<font face="MonoTR">WHERE approval_status=\'Pending\' ORDER BY id DESC</font> → 1.1 saniye, 1.148 satır.'), sp(3),
    labelrow('TEŞHİS','Seq Scan (533.657 satırdan 532.509’u elendi) + ayrı bir Sort adımı.'), sp(3),
    labelrow('DÜŞÜNCE','<font face="MonoTR">Pending</font> bir iş akışı durumu, toplamın sadece %0.2’si ve onaylanınca satır bu kümeden çıkıyor. '
        'Tüm tabloya indeks koymak yerine sadece bu küçük kümeye <b>partial (kısmi)</b> indeks ideal.', PURPLE), sp(3),
    labelrow('AKSİYON','', BLUE),
    codeblock(["CREATE INDEX CONCURRENTLY idx_profile_visits_pending",
               "  ON profile_visits (id DESC)",
               "  WHERE approval_status = 'Pending';"]), sp(4),
    labelrow('SONUÇ','<b>1.113 ms → 2.5 ms</b>. Tek indeks hem filtreyi hem <font face="MonoTR">ORDER BY id DESC</font>’i çözdü (Sort adımı yok oldu). İndeks minik kalır çünkü onaylananlar düşer.', GOOD),
])]
e += [sp(11)]

# 5.4 asset_document_dimensions
e += [KeepTogether([story_case('asset_document_dimensions', 'Lider kolon tuzağı'), sp(5),
    labelrow('BELİRTİ','<font face="MonoTR">WHERE asset_id = 175645</font> → 438 ms, 0 satır bile dönse tüm tablo taranıyordu.'), sp(3),
    labelrow('TEŞHİS','İlginç: <font face="MonoTR">asset_id</font> bir indekste vardı, ama '
        '<font face="MonoTR">(hotel_id, asset_id, ...)</font> şeklinde, <b>ikinci sırada</b>. Sorgu <font face="MonoTR">hotel_id</font> içermediği için o indeks kullanılamadı.'), sp(3),
    labelrow('DÜŞÜNCE','B-tree indeksi ancak <b>lider (ilk) kolonu</b> sorguda varsa devreye girer. Var olan indeks işe yaramıyordu.', PURPLE), sp(3),
    labelrow('AKSİYON','<font face="MonoTR">asset_id</font>’yi lider yapan yeni indeks:', BLUE),
    codeblock(["CREATE INDEX CONCURRENTLY idx_asset_doc_dims_asset_id",
               "  ON asset_document_dimensions (asset_id);"]), sp(4),
    labelrow('SONUÇ','<b>211 ms → 0.04 ms</b>. Ders: “indeks var” yetmez; <b>doğru kolonla</b> var mı bak.', GOOD),
])]
e += [sp(11)]

# 5.5 chatheadersforstaff, the epic
e += [KeepTogether([story_case('chatheadersforstaff', 'Kendini tekrarlayan view (destan)'), sp(5),
    labelrow('BELİRTİ','Staff sohbet paneli ağır açılıyordu. View’i çekince EXPLAIN <b>4.700 ms</b> gösterdi.'), sp(3),
    labelrow('TEŞHİS','View’in <font face="MonoTR">WHERE count &gt; 0</font> filtresi, son 3 aydaki <b>253.345</b> request_header’ın '
        '<b>her biri için</b> bir <font face="MonoTR">count</font> alt-sorgusu çalıştırıyordu (248 bin döngü), sonra 247.521’ini “hiç sohbeti yok” diye çöpe atıp 1.134 satır tutuyordu.'),
])]
e += [sp(4), labelrow('DÜŞÜNCE','Bu indeks sorunu değil, <b>tasarım</b> sorunuydu. Hiçbir indeks “248 bin kez döngü”yü çözemez. '
    '<font face="MonoTR">count &gt; 0</font> mantıken “en az bir sohbet var” demek, bunu <font face="MonoTR">EXISTS</font>’e '
    'çevirirsek planner semi-join yapıp küçük kümeden sürebilir.', PURPLE), sp(4)]
e += [labelrow('AKSİYON','View’i yeniden yazdık (<font face="MonoTR">count&gt;0</font> → <font face="MonoTR">EXISTS</font>) + profil sohbetleri için partial indeks:', BLUE), sp(3)]
e += [codeblock([
    "-- iç sorguya:",
    "AND EXISTS (SELECT 1 FROM chat_records_on_requests c",
    "            WHERE c.request_header_id = rh.id AND c.user_type='profil')",
    "",
    "CREATE INDEX CONCURRENTLY idx_cror_profil_header",
    "  ON chat_records_on_requests (request_header_id)",
    "  WHERE user_type = 'profil';",
]), sp(4)]
e += [labelrow('SONUÇ','İlk kazanım: <b>4.700 ms → ~1.000 ms.</b> 248 bin döngü gitti. Ama hikâye burada bitmedi…', GOOD), sp(8)]

e += [Paragraph('…ve bir kıl payı felaket', st_h3), sp(3)]
e += [labelrow('BELİRTİ','Gerçek kullanım <font face="MonoTR">hotel_id=673</font> ile 1.1 saniye sürüyordu, üstelik <b>0 satır</b> dönüyordu.'), sp(3)]
e += [labelrow('TEŞHİS','Chat tarafı hotel’i tanımıyordu; <b>tüm otellerin</b> 39.123 sohbet başlığını hash’liyordu. Tek otel istesek bile.'), sp(3)]
e += [labelrow('DÜŞÜNCE','<font face="MonoTR">chat_records</font>’ta <font face="MonoTR">hotel_id</font> vardı. '
    '“EXISTS’e <font face="MonoTR">c.hotel_id = rh.hotel_id</font> eklersek chat da hotel’e daralır” dedik. Cazip görünüyordu.', PURPLE), sp(3)]
e += [callout('<b>Önce doğruladık</b>, iyi ki: chat’in hotel_id’si her zaman header’ınkiyle aynı mı?', 'warn'), sp(4)]
e += [codeblock([
    "SELECT count(*) FROM chat_records_on_requests c",
    "JOIN request_headers rh ON rh.id = c.request_header_id",
    "WHERE c.hotel_id <> rh.hotel_id;   -- sonuç: 28.252 (!!)",
]), sp(4)]
e += [labelrow('DERS','28.252 satırda uyuşmuyorlardı. O “akıllı” koşulu eklesek view <b>sessizce yanlış sonuç</b> verecekti, '
    'kimse fark etmeden. Kıl payı. Her optimizasyonu uygulamadan önce varsayımını bir sorguyla doğrula.', HexColor('#b45309')), sp(4)]
e += [labelrow('AKSİYON','Onun yerine, view içindeki <b>gereksiz</b> <font face="MonoTR">ORDER BY send_time</font>’ı sildik '
    '(tüketici zaten <font face="MonoTR">ORDER BY id DESC</font> yapıyordu, view’in sıralaması boşa gidiyordu).', BLUE), sp(3)]
e += [labelrow('SONUÇ','Beklenmedik yan etki: planner <b>Merge Semi Join</b>’e geçti, chat tarafını sıralı okuyup '
    '<b>erken durdu</b> (85.890 yerine 1.828 satır). <b>4.700 ms → ~350 ms.</b> Bazen en iyi optimizasyon, fazlalığı silmektir.', GOOD)]
e += [sp(11)]

# 5.6 sahte yavaş
e += [KeepTogether([story_case('menu_item_catalog_groups', 'Sahte yavaş: suç DB’de değildi'), sp(5),
    labelrow('BELİRTİ','Logda <font face="MonoTR">menu_item_catalog_groups</font> sorgusu 475 ms görünüyordu.'), sp(3),
    labelrow('TEŞHİS','EXPLAIN: <b>0.078 ms.</b> İndeks zaten vardı, kusursuz çalışıyordu.'), sp(3),
    labelrow('DÜŞÜNCE','475 ms neredeydi? DB’de değil, o an bağlantı havuzu doluydu; süre <b>bağlantı bekleme + ağ + GORM eşleme</b>ydi. Log toplam süreyi yazar, saf DB süresini değil.', PURPLE), sp(3),
    labelrow('SONUÇ','DB tarafında yapılacak bir şey yoktu. Bağlantı düzeltmesi bu “sahte yavaş”ları da azalttı. Bu yüzden <b>Bölüm 0</b> var: önce ölç.', GOOD),
])]

# ============================================================ 6
e += [sp(14), section(6,'Tüm Sistemi Tarama (Proaktif)'), sp(7)]
e += [Paragraph('Log beklemek yerine, hangi tabloların sürekli tarandığını doğrudan PostgreSQL’e sorabilirsiniz.', st_body), sp(7)]
e += [Paragraph('A) En çok taranan tablolar', st_h3), sp(3)]
e += [codeblock([
    "SELECT relname AS tablo, seq_scan, seq_tup_read,",
    "       idx_scan, n_live_tup AS satir",
    "FROM pg_stat_user_tables",
    "WHERE seq_scan > 0 AND n_live_tup > 50000",
    "ORDER BY seq_tup_read DESC LIMIT 25;",
]), sp(4)]
e += [Paragraph('<font face="MonoTR">idx_scan</font> düşük + <font face="MonoTR">seq_tup_read</font> yüksek olan büyük tablolar = indeks kovalanacak baş adaylar.', st_muted), sp(8)]
e += [Paragraph('B) Gerçek yük: pg_stat_statements', st_h3), sp(3)]
e += [Paragraph('Bu eklenti açıksa, sorguları <b>toplam süreye</b> (kümülatif acı) göre sıralar, asıl darboğazı verir:', st_body), sp(4)]
e += [codeblock([
    "SELECT substring(query,1,10000) AS sorgu, calls,  -- tam sorgu, düzgün render",
    "       round(total_time::numeric/1000,1) AS toplam_sn,",
    "       round(mean_time::numeric,2) AS ort_ms, rows",
    "FROM pg_stat_statements",
    "ORDER BY total_time DESC LIMIT 30;",
]), sp(4)]
e += [Paragraph('Not: <font face="MonoTR">substring(query,1,10000)</font> kullanın. '
    '<font face="MonoTR">substring(query,1,80)</font> sorguyu 80 karakterde kesip okunamaz yapar; '
    'düz <font face="MonoTR">query</font> ise bazı client’larda devasa satırlarda bozuk görünür. '
    '<font face="MonoTR">1,10000</font> tam sorguyu verir ve düzgün render olur.', st_muted), sp(6)]
e += [callout('Öncesi/sonrası ölçmek için: indeksleri kurduktan sonra '
    '<font face="MonoTR">SELECT pg_stat_statements_reset();</font> ile sayaçları sıfırla, 30–60 dk canlı trafik bekle, tekrar bak. Eski canavarlar listeden düşmüş olmalı.', 'good')]

# ============================================================ 7
e += [sp(14), section(7,'Vaka: pg_stat_statements ve 505 Saatlik Canavar'), sp(7)]
e += [Paragraph('Sistemi tarayınca gerçek şok geldi. Loglar tek tek sorgu gösteriyordu; ama '
    '<font face="MonoTR">pg_stat_statements</font> <b>kümülatif</b> tabloyu açtı. Tepede beklenmedik bir isim vardı.', st_lead), sp(7)]
e += [labelrow('TEŞHİS','Tek bir sorgu, <font face="MonoTR">menu_item_catalog_prices WHERE catalog_id AND is_modifier</font>, '
    '<b>5.37 milyon</b> çağrı, ortalama 338 ms, toplam <b>505 SAAT</b> kümülatif. Tablonun tek indeksi yine <font face="MonoTR">pkey</font>’di.'), sp(4)]
e += [labelrow('AKSİYON','Filtre + sıralamayı karşılayan tek bileşik indeks:', BLUE), sp(3)]
e += [codeblock(["CREATE INDEX CONCURRENTLY idx_micp_catalog_modifier_priority",
                 "  ON menu_item_catalog_prices (menu_item_catalog_id, is_modifier, priority);"]), sp(4)]
e += [labelrow('SONUÇ','Ortalama 338 ms → &lt;2 ms. Aynı yöntemle <font face="MonoTR">permission_profiles</font> (45 saat), '
    '<font face="MonoTR">scheduled_mails</font> (118 saat), <font face="MonoTR">alpha_num_codes</font> (44 saat) de kapandı.', GOOD), sp(8)]

e += [Paragraph('Çıktıyı okurken üç kolon', st_h3), sp(3)]
e += [Paragraph('30 satırlık listeyi okurken panik yok, üç kolona bakılır: <font face="MonoTR">calls</font>, '
    '<font face="MonoTR">ort_ms</font>, <font face="MonoTR">rows</font>. Gerçek çıktıdan örnekler ve nasıl karar verildiği:', st_body), sp(5)]
e += [datatable(['Sorgu','calls','ort_ms','rows','Teşhis / Aksiyon'],
    [
        [Paragraph('tek büyük rapor',st_td), Paragraph('1',st_tdm), Paragraph('38.140',st_bad), Paragraph('10.619',st_tdm),
         Paragraph('Tek çağrı → nadir rapor. Yüksek ama sık değil. <b>Düşük öncelik.</b>',st_td)],
        [Paragraph('<font face="MonoTR">team_members</font>',st_td), Paragraph('12.432',st_tdm), Paragraph('2.0',st_td), Paragraph('—',st_tdm),
         Paragraph('Çok sık, hızlı. İndeks <font face="MonoTR">(hotel_id,user_id)</font> doğrula.',st_td)],
        [Paragraph('<font face="MonoTR">users ... not like</font>',st_td), Paragraph('647',st_tdm), Paragraph('11.6',st_td), Paragraph('4.188.031',st_bad),
         Paragraph('<b>4 milyon satır!</b> <font face="MonoTR">not like</font> indekslenemez → <b>uygulama sorunu.</b>',st_td)],
        [Paragraph('<font face="MonoTR">task_report_by_dep.</font>',st_td), Paragraph('2',st_tdm), Paragraph('1.420',st_bad), Paragraph('21.078',st_tdm),
         Paragraph('<font face="MonoTR">hotel_id</font>’ye indeks yok → <b>ekle.</b>',st_td)],
        [Paragraph('<font face="MonoTR">chatheadersforstaff</font>',st_td), Paragraph('108',st_tdm), Paragraph('101',st_good), Paragraph('—',st_tdm),
         Paragraph('Dün 4.700 ms’ti. <b>Optimize, iyi durumda.</b>',st_td)],
    ],
    [0.24,0.09,0.10,0.14,0.43])]
e += [sp(7), Paragraph('Karar verirken üç kural', st_h3), sp(3)]
e += [bullets([
    '<b>calls yüksek + ort_ms yüksek</b> = sistemik dert. Milyonlarca çağrı → <b>indeksle</b>, en yüksek getiri burada.',
    '<b>calls = 1 + ort_ms yüksek</b> = tek seferlik ağır rapor. EXPLAIN’le bak ama <b>düşük öncelik.</b>',
    '<b>rows devasa</b> (milyonlar) = uygulama gereğinden fazla veri çekiyor. Bu <b>indeks değil kod</b> sorunudur.',
    '<b>Fonksiyon/desen filtresi</b> (<font face="MonoTR">not like</font>, <font face="MonoTR">to_char(...)</font>) indeks kullanamaz → sorguyu/uygulamayı düzelt.',
])]

e += [sp(11), Paragraph('Taze bir çıktıyı aksiyona çevirmek', st_h3), sp(4)]
e += [Paragraph('Bu sorguyu her çalıştırdığında 30 satır gelir. Her satırı <b>dört kovadan</b> birine at, sonra kovaya göre davran:', st_body), sp(5)]
e += [bullets([
    '<font color="#4f46e5"><b>İNDEKS</b></font>: çok çağrılıyor ve yavaş. Filtre kolonuna bileşik indeks koy. En yüksek getiri burada.',
    '<font color="#0369a1"><b>KOD</b></font>: devasa satır döndürüyor ya da <font face="MonoTR">not like</font> / <font face="MonoTR">::date</font> gibi indekslenemez desen var. Sorguyu ya da uygulamayı düzelt.',
    '<font color="#6b7280"><b>TEK-SEFERLİK</b></font>: 1-2 çağrı, ağır ama nadir. Not al, ertele.',
    '<font color="#15803d"><b>TAMAM</b></font>: zaten hızlı ya da önceden optimize edilmiş. Dokunma.',
])]
e += [sp(6), Paragraph('Bir sonraki çekimden gerçek bir triyaj (toplam süreye göre sıralı):', st_body), sp(4)]
e += [datatable(['Sorgu','çağrı','ort_ms','Kova ve aksiyon'],
    [
        [Paragraph('<font face="MonoTR">team_members</font> (hotel+user)',st_td), Paragraph('19.520',st_tdm), Paragraph('2',st_td),
         Paragraph('<font color="#4f46e5"><b>İNDEKS</b></font> En yüksek toplam (39 sn). <font face="MonoTR">(hotel_id, user_id)</font> ekle.',st_td)],
        [Paragraph('kapasite: <font face="MonoTR">request_headers ⋈ request_lines</font>',st_td), Paragraph('283',st_tdm), Paragraph('119',st_td),
         Paragraph('<font color="#4f46e5"><b>İNDEKS</b></font> <font face="MonoTR">request_lines(request_header_id)</font> + <font face="MonoTR">::date</font> cast’ini kaldır.',st_td)],
        [Paragraph('oda-durumu (büyük CTE)',st_td), Paragraph('50',st_tdm), Paragraph('512',st_td),
         Paragraph('<font color="#4f46e5"><b>İNDEKS</b></font> EXPLAIN + <font face="MonoTR">guest_lists(hotel_id, room_number, checkin_date)</font>.',st_td)],
        [Paragraph('<font face="MonoTR">survey_researches</font> (item+rate_date)',st_td), Paragraph('27+27',st_tdm), Paragraph('~448',st_td),
         Paragraph('<font color="#4f46e5"><b>İNDEKS</b></font> <font face="MonoTR">(item_id, rate_date)</font> tek indeks iki sorguyu çözer.',st_td)],
        [Paragraph('<font face="MonoTR">building_id ... order_date::date</font>',st_td), Paragraph('17',st_tdm), Paragraph('1.431',st_bad),
         Paragraph('<font color="#0369a1"><b>KOD</b></font> <font face="MonoTR">::date</font> cast’i indeksi bozar. Aralık yaz.',st_td)],
        [Paragraph('<font face="MonoTR">users ... not like \'deleted%\'</font>',st_td), Paragraph('1.119',st_tdm), Paragraph('12',st_td),
         Paragraph('<font color="#0369a1"><b>KOD</b></font> 7,2 milyon satır dönüyor. Uygulama niye çekiyor?',st_td)],
        [Paragraph('<font face="MonoTR">buildings</font> gecikme raporu',st_td), Paragraph('1',st_tdm), Paragraph('38.140',st_bad),
         Paragraph('<font color="#6b7280"><b>TEK-SEFERLİK</b></font> Nadir. Not al, ertele.',st_td)],
        [Paragraph('<font face="MonoTR">chatheadersforstaff</font>',st_td), Paragraph('166',st_tdm), Paragraph('99',st_good),
         Paragraph('<font color="#15803d"><b>TAMAM</b></font> Dün optimize edildi. Dokunma.',st_td)],
    ],
    [0.27,0.09,0.09,0.55])]
e += [sp(6), callout('Öncelik sırası: önce dört <font color="#4f46e5"><b>İNDEKS</b></font> satırını kapat (birlikte ~100 sn kümülatif). '
    'Sonra <font face="MonoTR">::date</font> cast’lerini aralığa çevir. En son uygulama tarafındaki <font face="MonoTR">users</font> sorgusuna bak. '
    'Tek-seferlik raporları en sona bırak.', 'good')]

# ============================================================ 8
e += [sp(14), section(8,'Hangi İndeks? Hızlı Rehber'), sp(7)]
e += [datatable(['Sorgu deseni','Doğru indeks'],
    [
        [Paragraph('<font face="MonoTR">WHERE a = ?</font>',st_tdm), Paragraph('<font face="MonoTR">(a)</font>',st_tdm)],
        [Paragraph('<font face="MonoTR">WHERE a = ? AND b = ?</font>',st_tdm), Paragraph('<font face="MonoTR">(a, b)</font>',st_tdm)],
        [Paragraph('<font face="MonoTR">WHERE a = ? ORDER BY b</font>',st_tdm), Paragraph('<font face="MonoTR">(a, b)</font>, Sort adımını da siler',st_td)],
        [Paragraph('<font face="MonoTR">WHERE a = ? AND b BETWEEN x AND y</font>',st_tdm), Paragraph('<font face="MonoTR">(a, b)</font>',st_tdm)],
        [Paragraph('Join: <font face="MonoTR">ON t2.fk = t1.id</font>',st_tdm), Paragraph('t2 tarafında <font face="MonoTR">(fk)</font>',st_tdm)],
        [Paragraph('Tek değer çok sık (<font face="MonoTR">status=\'Pending\'</font>)',st_td), Paragraph('Partial: <font face="MonoTR">(id) WHERE status=\'Pending\'</font>',st_td)],
    ],
    [0.5,0.5])]
e += [sp(8), Paragraph('Üç altın kural', st_h3), sp(3)]
e += [bullets([
    '<b>Lider kolon:</b> indeksin ilk kolonu sorguda yoksa indeks kullanılmaz.',
    '<b>Eşitlik önce, aralık sonra:</b> <font face="MonoTR">(a, b)</font>’de <font face="MonoTR">a</font> eşitlik (=), <font face="MonoTR">b</font> aralık/sıralama olsun.',
    '<b>Fonksiyon kolonu bozar:</b> <font face="MonoTR">WHERE to_char(tarih)=...</font> indeks kullanamaz. <font face="MonoTR">tarih BETWEEN ...</font> yazın.',
])]

# ============================================================ 9
e += [sp(14), section(9,'Yaygın Tuzaklar (Anti-pattern’ler)'), sp(7)]
e += [Paragraph('Bu bir günde hepsiyle karşılaştık. Kaçının:', st_body), sp(6)]
traps = [
    ('SELECT * + limitsiz çekim', 'Bir sorgu 4 milyon satır döndürüyordu. İndeks çözmez, uygulama gereksiz veri çekiyor. Kolonları daralt, LIMIT/sayfalama kullan.'),
    ('Kolona fonksiyon uygulamak', '<font face="MonoTR">WHERE to_char(send_date,...)=...</font> ya da <font face="MonoTR">not like</font> indeksi devre dışı bırakır. Aralık/eşitlik yaz: <font face="MonoTR">send_date BETWEEN ...</font>.'),
    ('View içinde ORDER BY', 'Tüketici zaten sıralıyorsa view’in ORDER BY’ı boşa iştir, hatta iyi planı engeller. Sıralamayı çağıran tarafa bırakın.'),
    ('max_connections’ı çözüm sanmak', 'Havuzu sınırlamadan tavanı büyütmek semptomu erteler, RAM yer. Asıl ilaç <font face="MonoTR">MaxOpenConns</font>.'),
    ('Duplicate indeks', 'Aynı kolonlarda iki indeks çift yazma maliyeti. <font face="MonoTR">chat_records</font>’ta <font face="MonoTR">hotel_id</font>’ye iki indeks vardı, birini sildik.'),
    ('Doğrulamadan “akıllı” optimizasyon', 'Bir eşitlik varsaydık, 28.252 satırda tutmuyordu. Uygulasak sessiz veri hatası olurdu. Önce bir sorguyla doğrulayın.'),
]
for i,(t,d) in enumerate(traps):
    e += [labelrow('✕ '+str(i+1), '<b>'+t+'.</b> '+d, BAD), sp(3)]

# ============================================================ 10
e += [sp(12), section(10,'Sonuçlar, Komut Kartı & Kontrol Listesi'), sp(7)]
e += [Paragraph('Bir günde, bu yöntemle elde edilenler:', st_body), sp(5)]
e += [datatable(['Sorgu / Tablo','Önce','Sonra','Çözüm'],
    [
        ['menu_item_catalog_prices', Paragraph('338 ms',st_bad), Paragraph('&lt;2 ms',st_good), Paragraph('(catalog_id, is_modifier, priority)',st_tdm)],
        ['permission_profiles', Paragraph('12 ms',st_bad), Paragraph('&lt;1 ms',st_good), Paragraph('(user_id, hotel_id)',st_tdm)],
        ['survey_summaries', Paragraph('5.354 ms',st_bad), Paragraph('0.19 ms',st_good), Paragraph('(hotel_id, created_at)',st_tdm)],
        ['survey_researches (join)', Paragraph('441 ms',st_bad), Paragraph('0.22 ms',st_good), Paragraph('(request_id)',st_tdm)],
        ['profile_visits', Paragraph('1.113 ms',st_bad), Paragraph('2.5 ms',st_good), Paragraph('partial (Pending)',st_tdm)],
        ['asset_document_dimensions', Paragraph('211 ms',st_bad), Paragraph('0.04 ms',st_good), Paragraph('(asset_id)',st_tdm)],
        ['chatheadersforstaff (view)', Paragraph('4.700 ms',st_bad), Paragraph('~350 ms',st_good), Paragraph('rewrite + indeks',st_tdm)],
    ],
    [0.30,0.15,0.15,0.40])]
e += [sp(6), callout('Toplamda <b>~700 saat</b> kümülatif DB süresi ortadan kalktı. Bağlantı krizinin asıl kökü de buydu: '
    'yavaş sorgular bağlantıyı uzun tutuyordu. Sorgular hızlanınca havuz baskısı da düştü.', 'good')]

e += [sp(10), Paragraph('Komut Kartı: hepsi tek yerde', st_h3), sp(4)]
e += [codeblock([
    "-- TEŞHİS",
    "EXPLAIN (ANALYZE, BUFFERS) SELECT ... ;",
    "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='t';",
    "",
    "-- SİSTEM TARAMASI",
    "SELECT relname,seq_scan,idx_scan,n_live_tup FROM pg_stat_user_tables",
    "  WHERE n_live_tup>50000 ORDER BY seq_tup_read DESC LIMIT 25;",
    "SELECT substring(query,1,10000),calls,total_time,mean_time,rows  -- tam+düzgün",
    "  FROM pg_stat_statements ORDER BY total_time DESC LIMIT 30;",
    "",
    "-- İNDEKS",
    "CREATE INDEX CONCURRENTLY idx_t_kolon ON t (kolon);",
    "SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;  -- geçerlilik",
    "ANALYZE t;",
    "DROP INDEX gereksiz_indeks;",
    "",
    "-- BAĞLANTI",
    "SELECT client_addr,count(*) FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC;",
    "ALTER SYSTEM SET max_connections = 200;   -- restart ister",
]), sp(8)]

e += [Paragraph('Cep Kontrol Listesi', st_h3), sp(4)]
e += [checklist([
    'Sorgu gerçekten yavaş mı? → <font face="MonoTR">EXPLAIN (ANALYZE, BUFFERS)</font>',
    'Execution time mikrosaniye mi? → Sorun DB değil, havuz/ağ. Dur.',
    'Seq Scan mı görüyorum? → Filtre kolonuna indeks var mı? (<font face="MonoTR">pg_indexes</font>)',
    'İndeks var ama lider kolon yanlış mı? → Doğru sıralı yenisini kur.',
    '<font face="MonoTR">CREATE INDEX CONCURRENTLY</font> → <font face="MonoTR">ANALYZE</font> → tekrar EXPLAIN.',
    'rows devasa mı / <font face="MonoTR">not like</font>–<font face="MonoTR">to_char</font> var mı? → İndeks değil, uygulama/sorgu düzelt.',
    '“Akıllı” bir koşul mu ekliyorum? → Önce bir sorguyla varsayımı doğrula.',
    'Aynı işi yapan ikinci indeks var mı? → Sil.',
    'Bağlantı hatası mı? → <font face="MonoTR">MaxOpenConns × instance + 3 &lt; max_connections</font>',
])]
e += [sp(8), Paragraph('Son söz: en hızlı sorgu, hiç çalışmayan sorgudur; en iyi optimizasyon çoğu zaman '
    'bir indeks eklemek değil, gereksiz işi silmektir. Önce ölç, sonra düşün, en son yaz.', st_lead)]

OUT = sys.argv[1] if len(sys.argv)>1 else 'postgres_handbook.pdf'
render(OUT,
    badge='ŞİRKET İÇİ TEKNİK KILAVUZ',
    title='PostgreSQL Performans',
    subtitle='Yavaş Sorgu & İndeks El Kitabı',
    subline='PostgreSQL veritabanları için  ·  Uygulama: Go (database/sql)',
    desc_lines=[
        'Gerçek bir günün hikâyesi: “too many clients” hatasından başlayıp',
        'yarım milyon satırlık indekssiz tablolara, 505 saatlik sorgulara ve',
        'kendini tekrarlayan bir view’e kadar, adım adım, kopyala-çalıştır komutlarla.',
    ],
    meta_line='Temmuz 2026  ·  Yazılım Ekibi  ·  Hazırlayan: İbrahim Çobani',
    header_title='PostgreSQL Performans El Kitabı',
    header_sub='Yavaş Sorgu & İndeks · v1.0',
    footer_left='Teknolojiyi sadeleştiriyoruz, önce ölç, sonra indeksle.',
    story=e)
print('OK', OUT)
