# ajanlar

Claude Code'un çalıştırdığı alt ajanları (subagent) sağdaki bir panelde canlı gösterir. `/ajanlar` paneli açar, tekrar `/ajanlar` kapatır. Bir alt ajan başladığında panel kendiliğinden de açılır.

Panelde iki bölüm var:

- **Çalışıyor**: her ajan için renkli bir rol rozeti, görev numarası ve adı, saniye saniye ilerleyen süre, ajan tipi, model, araç ve hata sayısı. Altında son 18 adımı gösteren renkli bir şerit ve son araç çağrısı (hangi dosya, hangi komut) var.
- **Bitenler**: sonuç işareti (✔ bitti, ✖ hata/red, ■ yarıda kesildi), süre, bitiş saati ve ajanın cevabının ilk satırı. Hata alanlarda neden kırmızı yazılır.

En altta oturumun özeti yer alır: kaç ajan çalıştı, toplam süre ve en uzun süren ajan.

Rol, ajanın açıklamasından okunur. [superpowers](https://github.com/obra/superpowers)'ın `subagent-driven-development` akışındaki adlara göre ayarlıdır: **KODLA** (implementer), **SPEC** (spec review), **KALİTE** (code quality review), **TEST**, **KEŞİF** (Explore), **PLAN**. Tanınmayan açıklamalar **AJAN** olarak görünür.

Araç şeridindeki işaretler: ◇ dosya okuma, ⌕ arama, ✎ yazma/düzenleme, ▸ bash, ◎ web, ⬡ MCP, ★ skill, ◆ başka bir ajan.

Panel yalnız bu oturumdaki ajanları gösterir. Bir yere veri göndermez.

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install ajanlar@icitech
```

Sonra `/ajanlar` yazın.
