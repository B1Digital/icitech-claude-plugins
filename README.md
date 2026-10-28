# icitech Claude eklentileri

icitech team'in Claude Code için yaptığı eklentiler (mod'lar).

| Eklenti | Ne yapar |
|---|---|
| [harcama](plugins/harcama) | `/harcama` ile sağda bir panel açar: abonelik limitleri, ay takvimi, günlük harcama ve 5 saatlik blok |
| [ajanlar](plugins/ajanlar) | `/ajanlar` ile sağda bir panel açar: çalışan alt ajanlar canlı (rol, görev, süre, araç şeridi, sonuç) |

## Kurulum

Claude Code oturumunda:

```
/plugin marketplace add B1Digital/icitech-claude-plugins
/plugin install harcama@icitech
/plugin install ajanlar@icitech
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
