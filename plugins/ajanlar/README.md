# ajanlar

Claude Code'un çalıştırdığı alt ajanları (subagent) sağdaki bir panelde canlı gösterir. `/ajanlar` paneli açar, tekrar `/ajanlar` kapatır. Bir alt ajan başladığında panel kendiliğinden de açılır.

En üstte **ANA OTURUM** kartı durur: Claude'un kendisi (ana konuşma) çalışırken dönen işaret ve süre, araç sayısı, token ve tahmini maliyet, renkli araç şeridi ve son araç çağrısı. Sana cevap verip beklerken "bekliyor" yazar.

Bir **workflow** (Claude Code'un Workflow özelliği, `/workflows`) çalışınca mor bir blok açılır: workflow'un adı, süresi, maliyeti, ilerleme çubuğu (biten/başlayan ajan), ✔/✖/▶ sayıları, aşamaları ve o an çalışan ajanları. Workflow'un ajanları ayrı kart olarak listeyi doldurmaz, bloğun içinde görünür. Bitince blok iki satıra iner. Son 3 workflow gösterilir.

Ajan bölümleri:

- **Çalışıyor**: her ajan için renkli bir rol rozeti, görev numarası ve adı, saniye saniye ilerleyen süre, ajan tipi, model, araç ve hata sayısı. Altında son 18 adımı gösteren renkli bir şerit ve son araç çağrısı (hangi dosya, hangi komut) var.
- **Bitenler**: sonuç işareti (✔ bitti, ✖ hata/red, ■ yarıda kesildi), süre, bitiş saati ve ajanın cevabının ilk satırı. Hata alanlarda neden kırmızı yazılır.

Her ajan kartında token sayısı ve tahmini maliyet canlı artar (`↑182k ↓4.1k ~$0.42`). Tahmin, modelin liste fiyatıyla hesaplanır. Fiyatlar [LiteLLM'in herkese açık listesinden](https://github.com/BerriAI/litellm) (harcama panelinin kullandığı ccusage ile aynı kaynak) günde bir kez çekilir. İnternet yoksa son kaydedilen liste, o da yoksa eklentideki yedek tablo kullanılır. Abonelikle kullanıyorsan bu tutar API fiyatı karşılığıdır, ayrıca ödemezsin.

Panelin en altında sabit bir özet durur: kaç ajan çalıştı, toplam süre, en uzun süren ajan, ajanların tahmini toplam maliyeti ve oturumun kesin maliyeti (Claude Code'un verdiği, ana konuşma dahil).

Panel yeniden yüklenirse o an çalışan ajanların kartı geri gelir. Yeniden yüklemeden önceki adımları bilinmez.

Rol, ajanın açıklamasından okunur. [superpowers](https://github.com/obra/superpowers)'ın `subagent-driven-development` akışındaki adlara göre ayarlıdır: **KODLA** (implementer), **SPEC** (spec review), **KALİTE** (code quality review), **TEST**, **KEŞİF** (Explore), **PLAN**. Tanınmayan açıklamalar **AJAN** olarak görünür.

Araç şeridindeki işaretler: ◇ dosya okuma, ⌕ arama, ✎ yazma/düzenleme, ▸ bash, ◎ web, ⬡ MCP, ★ skill, ◆ başka bir ajan.

Panel yalnız bu oturumdaki ajanları gösterir. Bir yere veri göndermez.

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install ajanlar@icitech
```

Sonra `/ajanlar` yazın.
