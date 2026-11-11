# icitech Claude eklentileri

icitech team'in Claude Code için yaptığı eklentiler (mod'lar).

| Eklenti | Ne yapar |
|---|---|
| [harcama](plugins/harcama) | `/harcama` ile sağda bir panel açar: abonelik limitleri, ay takvimi, günlük harcama ve 5 saatlik blok |
| [ajanlar](plugins/ajanlar) | `/ajanlar` ile sağda bir panel açar: çalışan alt ajanlar canlı (rol, görev, süre, araç şeridi, sonuç) |
| [ici-internal-documents](plugins/ici-internal-documents) | icitech şablonunda Türkçe teknik doküman (PDF): kapak, İçindekiler, tablolar, akış şemaları, sade yazım |
| [ici-store-guard](plugins/ici-store-guard) | App Store ve Google Play'e göndermeden önce ret denetimi: kod, derlenmiş paket, mağaza görselleri, simülatörde reviewer testi; tek GO / NO-GO raporu |
| [ici-game-ads](plugins/ici-game-ads) | Mobil oyunlar için Google Ads reklam öğeleri: oyunun kendi görsellerinden sinematik videolar (dikey, yatay, kare) ve yazısız reklam görselleri |

## Kurulum

Claude Code oturumunda:

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install harcama@icitech
/plugin install ajanlar@icitech
/plugin install ici-internal-documents@icitech
/plugin install ici-store-guard@icitech
/plugin install ici-game-ads@icitech
```

Tek satırda da olur:

```
/plugin install harcama --marketplace B1Digital/icitech-claude-plugins
```

Terminalden:

```
claude plugin install harcama --marketplace B1Digital/icitech-claude-plugins
```

Masaüstü uygulamasında (`/plugin` çalışmıyorsa): mesaj kutusunun yanındaki **+** → **Plugins** → **Add marketplace** ile `B1Digital/icitech-claude-plugins`, sonra **Add plugin**.

Kurarken `Add marketplace?` sorusuna `y`, kapsam olarak da **user** seçin.
