import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderChildren } from 'claude-code'

import type { Block, Day, Month, Snapshot, Watch } from '../types'

const PANE = 'usage'
const TITLE = 'Harcama'

const snapshot = atom({ plugin: 'harcama', key: 'snapshot' } as const, null, {
  shape: 'snapshot-5',
})

const watch = atom({ plugin: 'harcama', key: 'watch' } as const, null, { shape: 'watch-1' })

const num = (v: unknown, fallback: number) => (typeof v === 'number' && v > 0 ? v : fallback)
const shortModel = (id: string) => id.match(/opus|sonnet|haiku|fable/)?.[0] ?? id

// Bütçe katı ve Opus uyarısı oturum başına bir kez; /clear startedAt'i değiştirir, sayaçlar sıfırlanır.
const observe = async ($: EngineInterface, usd: number, model: string | null, opts: { budget: number; opusAt: number }) => {
  const { startedAt } = await $.session.usage()
  const prev = await read($, watch)
  const w: Watch = prev && prev.startedAt === startedAt
    ? { ...prev, usd, model: model ?? prev.model }
    : { startedAt, usd, model: model ?? prev?.model ?? '', budgetStep: 0, opusHinted: false }
  const step = Math.floor(usd / opts.budget)
  if (step > w.budgetStep) {
    w.budgetStep = step
    $.ui.toast(`Bu oturum $${(step * opts.budget).toFixed(0)}'i geçti ($${usd.toFixed(2)}). İş bittiyse /clear ile yeni oturum daha ucuz.`)
  }
  if (!w.opusHinted && /opus/.test(w.model) && usd >= opts.opusAt) {
    w.opusHinted = true
    $.ui.toast(`Opus açık, oturum $${usd.toFixed(2)}. Deploy, issue, git gibi rutin işte /model sonnet yeter.`)
  }
  await update($, watch, () => w)
  $.ui.status(`oturum $${usd.toFixed(2)}${w.model ? ' · ' + shortModel(w.model) : ''}`)
}

const isOpen = async ($: EngineInterface) =>
  (await $.ui.panes()).some(pane => pane.id === PANE)

// A global `ccusage` if installed, else the pinned version through npx (first run downloads it).
const RUNNERS = [['ccusage'], ['npx', '-y', 'ccusage@20.0.42']]

const ccusage = async ($: EngineInterface, args: string[]) => {
  let lastError = 'ccusage çalıştırılamadı (Node.js kurulu mu?)'
  for (const runner of RUNNERS) {
    try {
      const { exitCode, stdout, stderr } = await $.process.run(
        [...runner, ...args, '--json', '--offline'],
        { timeoutMs: 120_000 },
      )
      if (exitCode === 0) return JSON.parse(stdout)
      lastError = stderr.trim() || `exit ${exitCode}`
    } catch (err) {
      lastError = String((err as Error).message ?? err)
    }
  }
  throw new Error(lastError)
}

// Who this machine belongs to: macOS full name, then git name, then login.
const NAME_SOURCES = [['id', '-F'], ['git', 'config', '--global', 'user.name'], ['whoami']]

const userName = async ($: EngineInterface) => {
  for (const argv of NAME_SOURCES) {
    try {
      const { exitCode, stdout } = await $.process.run(argv, { timeoutMs: 5_000 })
      if (exitCode === 0 && stdout.trim()) return stdout.trim()
    } catch {}
  }
  return ''
}

const pad = (n: number) => String(n).padStart(2, '0')
const ymd = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

const refresh = async ($: EngineInterface) => {
  let next: Snapshot
  try {
    const now = new Date()
    const today = ymd(now)
    const [user, blocks, daily] = await Promise.all([
      userName($),
      ccusage($, ['blocks', '--active']),
      ccusage($, ['daily', '--since', today.slice(0, 8).replaceAll('-', '') + '01']),
    ])
    const days: { period: string; totalCost: number; totalTokens: number }[] = daily.daily ?? []
    const month: Month = {
      todayCost: days.find(d => d.period === today)?.totalCost ?? 0,
      totalCost: days.reduce((sum, d) => sum + d.totalCost, 0),
      totalTokens: days.reduce((sum, d) => sum + d.totalTokens, 0),
      activeDays: days.length,
    }
    const calendar: Day[] = days.map(d => ({ date: d.period, cost: d.totalCost }))
    const raw = blocks.blocks?.[0]
    const block: Block | null = raw
      ? {
          startTime: raw.startTime,
          endTime: raw.endTime,
          costUSD: raw.costUSD,
          totalTokens: raw.totalTokens,
          costPerHour: raw.burnRate?.costPerHour ?? 0,
          projectedCost: raw.projection?.totalCost ?? raw.costUSD,
          projectedTokens: raw.projection?.totalTokens ?? raw.totalTokens,
        }
      : null
    next = { user, block, month, calendar, error: null, fetchedAt: Date.now() }
  } catch (err) {
    next = {
      user: '',
      block: null,
      month: null,
      calendar: [],
      error: String((err as Error).message ?? err),
      fetchedAt: Date.now(),
    }
  }
  await update($, snapshot, () => next)
}

const hm = (ms: number) => {
  const m = Math.max(0, Math.round(ms / 60_000))
  return `${Math.floor(m / 60)} sa ${m % 60} dk`
}
const clock = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const millions = (n: number) =>
  n >= 1e9 ? `${(n / 1e9).toFixed(2)} B` : `${(n / 1e6).toFixed(1)} M`
const MONTHS = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
const WEEKDAYS = ['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pz']
// Calendar cell inner width: fits "$1234" plus a space either side.
const CELL = 6
const TABLE_WIDTH = 7 * CELL + 8
const padLeft =(s: string) => ' '.repeat(Math.max(0, CELL - 1 - s.length))
const rule = (left: string, mid: string, right: string) =>
  left + Array(7).fill('─'.repeat(CELL)).join(mid) + right
const LIMIT_KINDS = [['five_hour', '5 saatlik'], ['seven_day', 'Haftalık']]
const limitColor = (pct: number) => (pct < 60 ? 'success' : pct < 85 ? 'warning' : 'error')
// Today: "02:00"; later: "Pzt 14:00".
const resetAt = (iso: string, now: Date) => {
  const d = new Date(iso)
  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  const sameDay = d.toDateString() === now.toDateString()
  return sameDay ? time : `${WEEKDAYS[(d.getDay() + 6) % 7]} ${d.getDate()} ${MONTHS[d.getMonth()]} ${time}`
}
// ponytail: fixed $/hour thresholds; tune if your normal pace differs
const rateColor = (perHour: number) =>
  perHour < 8 ? 'success' : perHour < 15 ? 'warning' : 'error'
const barParts = (pct: number, width = 20) => {
  const full = Math.round((pct / 100) * width)
  return ['━'.repeat(full), '─'.repeat(width - full)]
}

export const register: Register = (on, options) => {
  const opts = { budget: num(options.session_budget, 15), opusAt: num(options.opus_hint_at, 10) }
  const dailyTarget = num(options.daily_target, 40)
  let lastModel: string | null = null

  on('turn.complete', async ($, e, next) => {
    if (e.usage?.model) lastModel = e.usage.model
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    if (e.cost && e.changed.includes('cost')) await observe($, e.cost.usd, lastModel, opts)
    return next(e)
  })

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'harcama',
      description: 'Claude harcama panelini aç/kapat (5 saatlik blok + ay takvimi)',
    })
    // Poll only while the pane is up.
    $.clock.every(60_000, async () => {
      if (await isOpen($)) await refresh($)
    })

    return next(e)
  })

  on('command.run', { command: 'harcama' }, async $ => {
    if (await isOpen($)) {
      await $.ui.close({ id: PANE })
      return { text: 'Harcama paneli kapatıldı.' }
    }
    const opened = await $.ui.open({ id: PANE, title: TITLE })
    void refresh($)
    return {
      text: opened.isPlaced
        ? 'Harcama paneli açıldı.'
        : `Harcama paneli bekliyor: ${opened.reason}`,
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const snap = await read($, snapshot)

    if (!snap) return <Text dimColor>Yükleniyor…</Text>
    if (snap.error) return <Text color="error">ccusage hatası: {snap.error}</Text>
    const b = snap.block
    const m = snap.month
    const now = new Date()
    const start = b ? Date.parse(b.startTime) : 0
    const end = b ? Date.parse(b.endTime) : 0
    const pct = b ? Math.min(100, Math.round(((now.getTime() - start) / (end - start)) * 100)) : 0
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    // Calendar-day pace (idle days included), so the projection is not inflated.
    const monthEnd = m ? (m.totalCost / now.getDate()) * daysInMonth : 0

    const pace = b ? rateColor(b.costPerHour) : 'text'
    const avg = m ? m.totalCost / Math.max(1, m.activeDays) : 0
    const dayColor = (cost: number) => (cost <= avg ? 'success' : cost <= avg * 1.5 ? 'warning' : 'error')
    const todayColor = !m ? 'success' : m.todayCost > dailyTarget ? 'error' : dayColor(m.todayCost)
    const w = await read($, watch)

    // Month calendar: Monday-first rows, null pads the days before the 1st.
    const costs = new Map(snap.calendar.map(d => [Number(d.date.slice(8, 10)), d.cost]))
    const lead = (new Date(now.getFullYear(), now.getMonth(), 1).getDay() + 6) % 7
    const slots = [...Array(lead).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)]
    const weeks: (number | null)[][] = []
    while (slots.length % 7) slots.push(null)
    for (let i = 0; i < slots.length; i += 7) weeks.push(slots.slice(i, i + 7))

    // Subscription windows (five_hour, seven_day) from the last API response.
    const { rateLimits } = await $.session.usage()
    const limits = LIMIT_KINDS.flatMap(([kind, name]) => {
      const limit = rateLimits.find(l => l.kind === kind)
      return limit ? [{ name, ...limit }] : []
    })
    const label = (s: string) => <Text dimColor>{s.padEnd(11)}</Text>
    const row = (cells: RenderChildren[]) => (
      <Text>
        <Text dimColor>│</Text>
        {cells.map(c => [c, <Text dimColor>│</Text>])}
      </Text>
    )

    return (
      <Box flexDirection="column">
        <Box width={TABLE_WIDTH} justifyContent="space-between">
          <Text><Text bold color="claude">◆ icitech</Text><Text bold> team</Text></Text>
          <Text bold>{snap.user || 'harcama'}</Text>
        </Box>
        <Text color="claude">{'━'.repeat(TABLE_WIDTH)}</Text>
        <Text> </Text>
        <Text bold color="claude">{MONTHS[now.getMonth()]} {now.getFullYear()}</Text>
        <Text dimColor>{rule('┌', '┬', '┐')}</Text>
        {row(WEEKDAYS.map(d => [padLeft(d), <Text bold>{d}</Text>, ' ']))}
        <Text dimColor>{rule('├', '┼', '┤')}</Text>
        {weeks.map((week, i) => [
          row(week.map(day => {
            if (day === null) return ' '.repeat(CELL)
            const s = String(day)
            return [padLeft(s), day === now.getDate() ? <Text bold underline>{s}</Text> : <Text dimColor>{s}</Text>, ' ']
          })),
          row(week.map(day => {
            const cost = day === null ? 0 : (costs.get(day) ?? 0)
            if (day === null) return ' '.repeat(CELL)
            if (day > now.getDate() || cost === 0) return [padLeft('·'), <Text dimColor>·</Text>, ' ']
            const s = `$${Math.round(cost)}`
            return [padLeft(s), <Text color={dayColor(cost)} underline={day === now.getDate()}>{s}</Text>, ' ']
          })),
          <Text dimColor>{i === weeks.length - 1 ? rule('└', '┴', '┘') : rule('├', '┼', '┤')}</Text>,
        ])}
        <Text> </Text>
        <Text bold color="claude">Limitler</Text>
        {limits.length === 0 && <Text dimColor>Abonelik limiti bilgisi yok.</Text>}
        {limits.map(l => [
          <Text>
            {label(l.name)}
            <Text color={limitColor(l.percentUsed)}>{barParts(l.percentUsed)[0]}</Text>
            <Text dimColor>{barParts(l.percentUsed)[1]}</Text>
            {' '}<Text bold color={limitColor(l.percentUsed)}>%{Math.round(l.percentUsed)}</Text>
          </Text>,
          l.resetsAt ? <Text>{label('')}<Text dimColor>sıfırlanma {resetAt(l.resetsAt, now)}</Text></Text> : null,
        ])}
        <Text> </Text>
        <Text bold color="claude">Bu ay</Text>
        {w && <Text>{label('Oturum')}<Text bold color={w.usd >= opts.budget ? 'warning' : 'suggestion'}>${w.usd.toFixed(2)}</Text>{w.model ? <Text dimColor> · {shortModel(w.model)}</Text> : null}</Text>}
        {!m && <Text dimColor>Veri yok.</Text>}
        {m && <Text>{label('Bugün')}<Text bold color={todayColor}>${m.todayCost.toFixed(2)}</Text> <Text dimColor>/ hedef ${dailyTarget}</Text></Text>}
        {m && <Text>{label('Toplam')}<Text bold color="suggestion">${m.totalCost.toFixed(2)}</Text> <Text dimColor>· {millions(m.totalTokens)}</Text></Text>}
        {m && <Text>{label('Ortalama')}${avg.toFixed(2)} / gün <Text dimColor>({m.activeDays} aktif gün)</Text></Text>}
        {m && <Text>{label('Ay sonu')}<Text color="warning">~${monthEnd.toFixed(0)}</Text></Text>}
        <Text> </Text>
        <Text bold color="claude">5 saatlik blok</Text>
        {!b && <Text dimColor>Aktif blok yok.</Text>}
        {b && <Text><Text color={pace}>{barParts(pct)[0]}</Text><Text dimColor>{barParts(pct)[1]}</Text> {pct}%</Text>}
        {b && <Text>{label('Saat')}{clock(b.startTime)} → {clock(b.endTime)}</Text>}
        {b && <Text>{label('Kalan')}{hm(end - now.getTime())}</Text>}
        {b && <Text>{label('Maliyet')}<Text bold color="suggestion">${b.costUSD.toFixed(2)}</Text> <Text dimColor>· {millions(b.totalTokens)}</Text></Text>}
        {b && <Text>{label('Hız')}<Text color={pace}>${b.costPerHour.toFixed(2)} / sa</Text></Text>}
        {b && <Text>{label('Tahmin')}<Text color={pace}>${b.projectedCost.toFixed(2)}</Text></Text>}
        <Text> </Text>
        <Text dimColor>Güncelleme {clock(new Date(snap.fetchedAt).toISOString())} · /harcama kapatır</Text>
      </Box>
    )
  })
}
