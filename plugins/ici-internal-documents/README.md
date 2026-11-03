# ici-internal-documents

icitech kurumsal şablonunda Türkçe teknik doküman (PDF) üreten skill.

- Koyu indigo kapak, otomatik İçindekiler, numaralı bölümler, başlık/altbilgi
- Veri tabloları, uyarı kutuları, önce/sonra kartları, kod blokları, vaka kalıbı
- `figure()` ile Graphviz akış şemaları
- Çıktı her zaman Türkçe; sade yazım kuralları [simpleenglish](https://github.com/aminblg/simpleenglish)'ten Türkçeye uyarlandı

## Kurulum

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install ici-internal-documents@icitech
```

Gereken: Python 3 ve `reportlab` (skill ilk kullanımda `/tmp/icidoc_venv` kurar), önizleme için `pdftoppm`, şemalar için Graphviz (`dot`). Fontlar macOS Arial; yoksa DejaVu'ya düşer.

## Kullanım

Claude Code'a "icitech şablonunda teknik doküman hazırla" deyin. Örnek içerik: `skills/ici-internal-documents/assets/example_postgres_handbook.py`.
