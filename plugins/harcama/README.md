# harcama

Claude Code kullanımını sağda açılan bir panelde gösterir. `/harcama` paneli açar, tekrar `/harcama` kapatır.

Panelde üç bölüm var:

- **Ay takvimi**: her günün harcaması, ortalamaya göre renkli (yeşil altında, sarı 1,5 katına kadar, kırmızı üstünde). Bugün altı çizili.
- **Bu ay**: bugün, toplam, aktif gün ortalaması, ay sonu tahmini.
- **5 saatlik blok**: ilerleme çubuğu, kalan süre, maliyet, saatlik hız ve blok sonu tahmini.

Panel açıkken dakikada bir yenilenir; kapalıyken hiçbir şey çalıştırmaz.

## Gereksinim

Bilgisayarda **Node.js** kurulu olmalı. Veriler [ccusage](https://github.com/ryoppippi/ccusage) ile kendi makinendeki Claude Code kayıtlarından okunur; dışarı bir şey gönderilmez. ccusage kurulu değilse ilk açılışta `npx` ile indirilir (birkaç saniye sürebilir).

Gösterilen dolar tutarı, aynı kullanımın API fiyatıyla karşılığıdır. Abonelikle (Pro/Max/Team) kullanıyorsan bu tutarı ayrıca ödemezsin.

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install harcama@icitech
```

Sonra `/harcama` yazın.
