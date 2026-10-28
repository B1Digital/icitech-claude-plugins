import { atom, read, update } from 'claude-code'
import type { Color, EngineInterface, ModelUsage, Register } from 'claude-code'

import type { Main, Run, RunStatus, Workflow } from '../types'

const PANE = 'agents'
const TITLE = 'Ajanlar'
const KEEP = 40
const STRIP = 18

const runs = atom({ plugin: 'ajanlar', key: 'runs' } as const, [], { shape: 'runs-3' })
const IDLE: Main = { busy: false, since: 0, tools: 0, errors: 0, recent: [], last: null, tokensIn: 0, tokensOut: 0, usd: 0 }
const main = atom({ plugin: 'ajanlar', key: 'main' } as const, IDLE, { shape: 'main-1' })
const workflows = atom({ plugin: 'ajanlar', key: 'workflows' } as const, [], { shape: 'workflows-1' })

const isOpen = async ($: EngineInterface) =>
  (await $.ui.panes()).some(pane => pane.id === PANE)

// Redraw ticks only while something runs; module state is rebuilt on reload, which only pauses the spinner.
let running = 0
let mainBusy = false
const recount = (list: Run[]) => {
  running = list.filter(r => r.status === 'running').length
  return list
}
const patch = ($: EngineInterface, match: (r: Run) => boolean, fn: (r: Run) => Run) =>
  update($, runs, list => recount(list.map(r => (match(r) ? fn(r) : r))))

type Role = { label: string; color: Color }
// Roles come from the Agent call's description (superpowers: "Implement Task 2: …", "Spec review Task 2").
const roleOf = (r: Run): Role => {
  const d = `${r.description} ${r.subagentType}`.toLowerCase()
  const review = /review|reviewer|incele|denetle/.test(d)
  if (review && /spec|uyum/.test(d)) return { label: 'SPEC', color: 'suggestion' }
  if (review && /quality|kalite/.test(d)) return { label: 'KALİTE', color: 'permission' }
  if (review) return { label: 'REVIEW', color: 'permission' }
  if (/\btest/.test(d)) return { label: 'TEST', color: 'success' }
  if (/implement|uygula|kodla|\bfix|düzelt|\bcode\b/.test(d)) return { label: 'KODLA', color: 'claude' }
  if (r.subagentType === 'Explore' || /explore|ara|keşif/.test(d)) return { label: 'KEŞİF', color: 'ide' }
  if (r.subagentType === 'Plan' || /\bplan/.test(d)) return { label: 'PLAN', color: 'planMode' }
  if (r.subagentType === 'fork') return { label: 'FORK', color: 'merged' }
  return { label: 'AJAN', color: 'remember' }
}
const taskOf = (r: Run) => r.description.match(/(?:task|görev)\s*#?(\d+)/i)?.[1] ?? null

const GLYPHS: [RegExp, string, Color][] = [
  [/^(Read|NotebookRead)$/, '◇', 'suggestion'],
  [/^(Grep|Glob|LS)$/, '⌕', 'suggestion'],
  [/^(Edit|Write|MultiEdit|NotebookEdit)$/, '✎', 'claude'],
  [/^Bash$/, '▸', 'warning'],
  [/^(WebFetch|WebSearch)$/, '◎', 'permission'],
  [/^Agent$/, '◆', 'merged'],
  [/^Skill$/, '★', 'remember'],
  [/^mcp__/, '⬡', 'ide'],
  [/^(TodoWrite|Task)/, '☐', 'subtle'],
]
const glyph = (tool: string): [string, Color] => {
  const hit = GLYPHS.find(([re]) => re.test(tool))
  return hit ? [hit[1], hit[2]] : ['•', 'text']
}

// A Workflow call's script starts with `export const meta = { name, phases: [{ title }] }`; a saved one goes by `name`.
const workflowOf = (id: string, args: Record<string, unknown>): Workflow => {
  const script = typeof args.script === 'string' ? args.script : ''
  const meta = script.match(/meta\s*=\s*\{([\s\S]*?)\n\}/)?.[1] ?? script.slice(0, 2000)
  const name = meta.match(/name\s*:\s*['"`]([^'"`]+)/)?.[1]
    ?? (typeof args.name === 'string' ? args.name : null)
    ?? (typeof args.scriptPath === 'string' ? base(args.scriptPath).replace(/\.[jt]s$/, '') : 'workflow')
  const phases = [...(meta.match(/phases\s*:\s*\[([\s\S]*?)\]/)?.[1] ?? '').matchAll(/title\s*:\s*['"`]([^'"`]+)/g)].map(m => m[1]!)
  return { id, name, phases, startedAt: Date.now() }
}

const base = (p: unknown) => (typeof p === 'string' ? p.split('/').pop() ?? p : '')
const cut = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s)
const detail = (tool: string, args: Record<string, unknown>) => {
  const target =
    base(args.file_path ?? args.notebook_path) ||
    (typeof args.description === 'string' && args.description) ||
    (typeof args.command === 'string' && args.command) ||
    (typeof args.pattern === 'string' && args.pattern) ||
    (typeof args.url === 'string' && args.url) ||
    (typeof args.skill === 'string' && args.skill) ||
    ''
  return cut(`${tool.replace(/^mcp__([^_]+)__/, '$1:')} ${String(target).split('\n')[0]}`.trim(), 60)
}

const mmss = (ms: number) => {
  const s = Math.max(0, Math.round(ms / 1000))
  return s >= 3600
    ? `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
    : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
const clock = (t: number) => {
  const d = new Date(t)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const shortModel = (m: string) => m.replace(/^claude-/, '').replace(/-\d{8}$/, '')
type Price = [input: number, cacheWrite: number, cacheRead: number, output: number]   // USD per million tokens

// Prices come from LiteLLM's public list (the one ccusage, and so the harcama panel, uses), refreshed daily
// and kept in the store; the table below is only the fallback when the list is unreachable or lacks a model.
const PRICE_URL = 'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json'
const PRICE_TTL = 24 * 3600_000
let priceBook: Record<string, Price> = {}

const loadPrices = async ($: EngineInterface) => {
  const kept = (await $.store.get('prices')) as { at: number; book: Record<string, Price> } | undefined
  if (kept) priceBook = kept.book
  if (kept && Date.now() - kept.at < PRICE_TTL) return
  try {
    const res = await $.http.fetch(PRICE_URL)
    if (!res.ok) return
    const all = JSON.parse(res.text) as Record<string, Record<string, unknown>>
    const book: Record<string, Price> = {}
    for (const [id, p] of Object.entries(all)) {
      if (!id.startsWith('claude-') || typeof p.input_cost_per_token !== 'number' || typeof p.output_cost_per_token !== 'number') continue
      const m = (v: unknown, or: number) => (typeof v === 'number' ? v : or) * 1e6
      book[id] = [m(p.input_cost_per_token, 0), m(p.cache_creation_input_token_cost, p.input_cost_per_token as number),
        m(p.cache_read_input_token_cost, p.input_cost_per_token as number), m(p.output_cost_per_token, 0)]
    }
    if (Object.keys(book).length === 0) return
    priceBook = book
    await $.store.set('prices', { at: Date.now(), book })
  } catch {}   // offline: the kept list or the fallback table stays
}

// Fallback (platform.claude.com/docs/en/about-claude/pricing, 2026-10-28); cache writes priced at 5m.
const PRICES: [RegExp, number, number, number, number][] = [
  [/fable-5-1|mythos-5-1/, 10, 12.5, 0.25, 50],
  [/fable-5/, 10, 12.5, 1, 50],
  [/opus-5-5/, 4, 5, 0.2, 20],
  [/opus-4-1|opus-4-2025|opus-4$/, 15, 18.75, 1.5, 75],
  [/opus-(5|4-[5-8])/, 5, 6.25, 0.5, 25],
  [/sonnet-5-5/, 2, 2.5, 0.1, 10],
  [/sonnet-5/, 2, 2.5, 0.2, 10],
  [/sonnet-4/, 3, 3.75, 0.3, 15],
  [/haiku-4-5/, 1, 1.25, 0.1, 5],
]
const costOf = (model: string, u: ModelUsage): number | null => {
  const prompt = u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens
  const id = model.replace(/-\d{8}$/, '')
  // Haiku 5.5's pricier tier over 100k prompt tokens is not in LiteLLM's list.
  const row: Price | undefined = /haiku-5-5/.test(model) && prompt > 100_000
    ? [0.5, 0.625, 0.05, 2.5]
    : priceBook[model] ?? priceBook[id] ?? (PRICES.find(([re]) => re.test(model))?.slice(1) as Price | undefined)
  if (!row) return null
  const [inp, write, read, out] = row
  return (u.input_tokens * inp + u.cache_creation_input_tokens * write + u.cache_read_input_tokens * read + u.output_tokens * out) / 1e6
}
const tokens = (n: number) =>
  n < 1000 ? String(n) : n < 1e6 ? `${(n / 1000).toFixed(n < 10_000 ? 1 : 0)}k` : `${(n / 1e6).toFixed(1)}M`
const usd = (n: number) => (n < 0.01 ? '<$0.01' : `$${n.toFixed(2)}`)

const SPIN = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
const STATUS: Record<Exclude<RunStatus, 'running'>, [string, Color]> = {
  done: ['✔', 'success'],
  failed: ['✖', 'error'],
  aborted: ['■', 'warning'],
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'ajanlar',
      description: 'Alt ajan panelini aç/kapat (canlı rol, görev, süre, araçlar)',
    })
    $.clock.every(400, () => {
      if (running > 0 || mainBusy) $.ui.invalidate('ui.render')
    })
    void loadPrices($)
    $.clock.every(3600_000, () => void loadPrices($))
    await update($, main, m => ((mainBusy = m.busy), m))   // a reload keeps the spinner going mid-turn
    // After a reload (or a state reset) agents already running get their card back; what they did before is unknown.
    const known = await $.agent.list()
    await update($, runs, list => recount([
      ...list,
      ...known
        .filter(a => (a.status === 'running' || a.status === 'pending') && !list.some(r => r.agentId === a.id))
        .map((a): Run => ({
          key: `adopted:${a.id}`, agentId: a.id, parentAgentId: a.parentId ?? null, description: a.description,
          subagentType: a.type, model: '?', background: true, startedAt: Date.now(), endedAt: null, status: 'running',
          tools: 0, errors: 0, recent: [], last: null, note: null, tokensIn: 0, tokensOut: 0, usd: 0,
          workflowId: null, workflowIndex: null,
        })),
    ].slice(-KEEP)))
    return next(e)
  })

  on('command.run', { command: 'ajanlar' }, async $ => {
    if (await isOpen($)) {
      await $.ui.close({ id: PANE })
      return { text: 'Ajan paneli kapatıldı.' }
    }
    const opened = await $.ui.open({ id: PANE, title: TITLE })
    return {
      text: opened.isPlaced ? 'Ajan paneli açıldı.' : `Ajan paneli bekliyor: ${opened.reason}`,
    }
  })

  on('agent.spawn', async ($, e, next) => {
    if (e.resume) {
      const id = e.resume.agentId
      await patch($, r => r.agentId === id, r => ({ ...r, status: 'running', endedAt: null, note: null }))
      return next(e)
    }
    const key = `${e.tool_use_id}:${e.workflow?.agentIndex ?? ''}`
    const run: Run = {
      key,
      agentId: null,
      parentAgentId: e.parentAgentId ?? null,
      description: e.description,
      subagentType: e.subagentType,
      model: e.model ?? e.parentModel,
      background: e.background,
      startedAt: Date.now(),
      endedAt: null,
      status: 'running',
      tools: 0,
      errors: 0,
      recent: [],
      last: null,
      note: null,
      tokensIn: 0,
      tokensOut: 0,
      usd: 0,
      workflowId: e.workflow ? e.tool_use_id : null,
      workflowIndex: e.workflow?.agentIndex ?? null,
    }
    // A workflow agent whose Workflow call this load did not see (resumed run, reload) still gets a group.
    if (e.workflow) await update($, workflows, list => list.some(w => w.id === e.tool_use_id) ? list
      : [...list, { id: e.tool_use_id, name: 'workflow', phases: [], startedAt: Date.now() }].slice(-10))
    await update($, runs, list => recount([...list, run].slice(-KEEP)))
    if (!(await isOpen($))) void $.ui.open({ id: PANE, title: TITLE })

    const res = await next(e)
    if (res.deny !== undefined) {
      await patch($, r => r.key === key, r => ({ ...r, status: 'failed', endedAt: Date.now(), note: cut(res.deny ?? '', 80) }))
    } else {
      await patch($, r => r.key === key, r => ({ ...r, agentId: res.agentId ?? null, model: res.model || r.model }))
    }
    return res
  })

  on('tool.call', async ($, e, next) => {
    const id = e.agentId
    const args = e as unknown as Record<string, unknown>
    if (!id) {
      // The main conversation's own calls feed the ANA OTURUM card; a Workflow call opens a group.
      const flow = e.tool === 'Workflow' ? workflowOf(e.tool_use_id, args) : null
      if (flow) await update($, workflows, list => [...list, flow].slice(-10))
      const last = flow ? `Workflow ${flow.name}` : detail(e.tool, args)
      await update($, main, m => ({ ...m, tools: m.tools + 1, recent: [...m.recent, e.tool].slice(-STRIP), last }))
      const ran = await next(e)
      if (ran.isError) await update($, main, m => ({ ...m, errors: m.errors + 1 }))
      return ran
    }
    const last = detail(e.tool, args)
    await patch($, r => r.agentId === id, r => ({
      ...r,
      tools: r.tools + 1,
      recent: [...r.recent, e.tool].slice(-STRIP),
      last,
    }))
    const ran = await next(e)
    if (ran.isError) await patch($, r => r.agentId === id, r => ({ ...r, errors: r.errors + 1 }))
    return ran
  })

  // Every model request of a subagent: tokens and an estimated cost add up live.
  on('turn.step', async function* ($, e, next) {
    const ran = yield* next(e)
    const id = e.agentId
    const u = ran?.usage
    if (!id && u) {
      const cost = costOf(u.model, u)
      await update($, main, m => ({
        ...m,
        tokensIn: m.tokensIn + u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens,
        tokensOut: m.tokensOut + u.output_tokens,
        usd: m.usd === null || cost === null ? null : m.usd + cost,
      }))
    }
    if (id && u) {
      const cost = costOf(u.model, u)
      await patch($, r => r.agentId === id, r => ({
        ...r,
        tokensIn: r.tokensIn + u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens,
        tokensOut: r.tokensOut + u.output_tokens,
        usd: r.usd === null || cost === null ? null : r.usd + cost,
      }))
    }
    return ran
  })

  on('turn.start', async ($, e, next) => {
    if (!e.agentId) {
      mainBusy = true
      await update($, main, m => ({ ...m, busy: true, since: Date.now() }))
    }
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const id = e.agentId
    if (!id) {
      mainBusy = false
      await update($, main, m => ({ ...m, busy: false, since: Date.now() }))
    }
    if (id) {
      const status: RunStatus = e.isAborted ? 'aborted' : e.reason === 'answer' ? 'done' : 'failed'
      // First non-empty answer line without markdown marks (### heading, **bold**, - list, `code`).
      const line = (e.answer ?? '').split('\n')
        .map(l => l.replace(/^\s*(#{1,6}\s+|[-*>]\s+)/, '').replace(/\*\*|`/g, '').trim())
        .find(Boolean) ?? ''
      const note = cut(line, 90) || null
      await patch($, r => r.agentId === id && r.status === 'running', r => ({ ...r, status, endedAt: Date.now(), note }))
    }
    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, runs)
    const now = Date.now()
    const width = Math.max(30, Math.min(64, (e.viewport?.columns ?? 60) - 2))
    // The body's real height (the frame's own rows already taken off); the viewport is the whole terminal.
    const rows = Math.max(10, e.props.scroll?.bodyRows ?? (e.viewport?.rows ?? 30) - 8)
    const room = rows
    const spin = SPIN[Math.floor(now / 100) % SPIN.length]

    const m = await read($, main)
    const flows = await read($, workflows)
    // Workflow agents are drawn inside their workflow's block, not as cards of their own.
    const plain = list.filter(r => !r.workflowId)
    const live = plain.filter(r => r.status === 'running')
    const ended = plain.filter(r => r.status !== 'running').sort((a, b) => (b.endedAt ?? 0) - (a.endedAt ?? 0))
    const count = (s: RunStatus) => list.filter(r => r.status === s).length
    const totalMs = list.reduce((sum, r) => sum + ((r.endedAt ?? now) - r.startedAt), 0)
    const longest = list.reduce<Run | null>((best, r) => {
      const ms = (r.endedAt ?? now) - r.startedAt
      return !best || ms > (best.endedAt ?? now) - best.startedAt ? r : best
    }, null)
    const agentsUsd = list.reduce((sum, r) => sum + (r.usd ?? 0), 0)
    const { cost } = await $.session.usage()

    const badge = (r: Run) => {
      const role = roleOf(r)
      return <Text backgroundColor={role.color} color="inverseText" bold>{` ${role.label} `}</Text>
    }
    const title = (r: Run, max: number) => {
      const task = taskOf(r)
      const text = cut(
        r.description
          .replace(/^(implement|review|spec review|code quality review)\s*/i, '')
          .replace(task ? /(task|görev)\s*#?\d+\s*[:\-–]?\s*/i : /$^/, ''),
        max,
      ) || r.subagentType
      return (
        <Text>
          {task && <Text bold color={roleOf(r).color}>#{task} </Text>}
          <Text bold>{text}</Text>
        </Text>
      )
    }
    const strip = (r: Run) => (
      <Text>
        {r.recent.map(t => {
          const [g, c] = glyph(t)
          return <Text color={c}>{g}</Text>
        })}
        {r.recent.length === 0 && <Text dimColor>· başlıyor</Text>}
      </Text>
    )
    const meta = (r: Run) => (
      <Text dimColor>
        {r.subagentType} · {shortModel(r.model)} · {r.tools} araç
        {r.errors > 0 && <Text color="error"> · {r.errors} hata</Text>}
        {r.background && ' · arka plan'}
      </Text>
    )
    const spend = (r: Run) => (
      <Text>
        <Text dimColor>↑</Text>{tokens(r.tokensIn)} <Text dimColor>↓</Text>{tokens(r.tokensOut)}
        {r.usd !== null && <Text bold color="suggestion"> ~{usd(r.usd)}</Text>}
      </Text>
    )
    const indent = (r: Run) => (r.parentAgentId ? '  ' : '')

    const liveCard = (r: Run) => {
      const role = roleOf(r)
      return [
        <Box width={width} justifyContent="space-between">
          <Text>
            {indent(r)}
            <Text color={role.color} bold>{spin} </Text>
            {badge(r)} {title(r, width - 24)}
          </Text>
          <Text bold color={role.color}>{mmss(now - r.startedAt)}</Text>
        </Box>,
        <Text>{indent(r)}<Text color={role.color}>  │ </Text>{meta(r)}</Text>,
        <Text>{indent(r)}<Text color={role.color}>  │ </Text>{spend(r)}</Text>,
        <Text>{indent(r)}<Text color={role.color}>  │ </Text>{strip(r)}</Text>,
        <Text>{indent(r)}<Text color={role.color}>  └ </Text><Text>{r.last ?? <Text dimColor>ilk adım bekleniyor</Text>}</Text></Text>,
        <Text> </Text>,
      ]
    }
    const endedRow = (r: Run) => {
      const [mark, color] = STATUS[r.status as Exclude<RunStatus, 'running'>]
      return [
        <Box width={width} justifyContent="space-between">
          <Text>{indent(r)}<Text color={color} bold>{mark} </Text>{badge(r)} {title(r, width - 30)}</Text>
          <Text><Text color={color}>{mmss((r.endedAt ?? now) - r.startedAt)}</Text> <Text dimColor>{clock(r.endedAt ?? now)}</Text></Text>
        </Box>,
        r.note && r.status !== 'done'
          ? <Text>{indent(r)}  <Text color={color}>↳ {cut(r.note, width - 6)}</Text></Text>
          : <Text>{indent(r)}  <Text dimColor>{r.tools} araç · </Text>{r.usd !== null ? <Text color="suggestion">~{usd(r.usd)}</Text> : <Text dimColor>{tokens(r.tokensIn + r.tokensOut)} tok</Text>}<Text dimColor>{r.note ? ` · ${cut(r.note, width - 24)}` : ''}</Text></Text>,
      ]
    }

    const stripOf = (recent: string[]) => (
      <Text>
        {recent.map(t => {
          const [g, c] = glyph(t)
          return <Text color={c}>{g}</Text>
        })}
      </Text>
    )
    const mainCard = [
      <Box width={width} justifyContent="space-between">
        <Text>
          <Text color={m.busy ? 'claude' : 'subtle'} bold>{m.busy ? spin : '●'} </Text>
          <Text backgroundColor="claude" color="inverseText" bold>{' ANA OTURUM '}</Text>
          <Text bold color={m.busy ? 'claude' : undefined} dimColor={!m.busy}>{m.busy ? ' çalışıyor' : ' bekliyor'}</Text>
        </Text>
        <Text bold={m.busy} color={m.busy ? 'claude' : undefined} dimColor={!m.busy}>{m.since ? mmss(now - m.since) : ''}</Text>
      </Box>,
      <Text>
        <Text color="claude">  │ </Text>
        <Text dimColor>{m.tools} araç{m.errors > 0 ? '' : ' · '}</Text>
        {m.errors > 0 && <Text color="error"> · {m.errors} hata · </Text>}
        <Text dimColor>↑</Text>{tokens(m.tokensIn)} <Text dimColor>↓</Text>{tokens(m.tokensOut)}
        {m.usd !== null && <Text bold color="suggestion"> ~{usd(m.usd)}</Text>}
      </Text>,
      <Text><Text color="claude">  │ </Text>{m.recent.length ? stripOf(m.recent) : <Text dimColor>henüz araç çağrısı yok</Text>}</Text>,
      <Text><Text color="claude">  └ </Text>{m.last ? <Text dimColor={!m.busy}>{m.last}</Text> : <Text dimColor>—</Text>}</Text>,
    ]

    // Newest workflows first; a running one shows its live agents, a finished one folds into a line.
    const flowBlocks = flows.slice(-3).reverse().flatMap(w => {
      const agents = list.filter(r => r.workflowId === w.id)
      if (agents.length === 0 && now - w.startedAt > 10 * 60_000) return []
      const going = agents.filter(r => r.status === 'running').sort((a, b) => (a.workflowIndex ?? 0) - (b.workflowIndex ?? 0))
      const done = agents.filter(r => r.status === 'done').length
      const bad = agents.filter(r => r.status === 'failed' || r.status === 'aborted').length
      const isLive = going.length > 0 || agents.length === 0
      const end = isLive ? now : Math.max(...agents.map(r => r.endedAt ?? now))
      const spent = agents.reduce((sum, r) => sum + (r.usd ?? 0), 0)
      const headline = (
        <Box width={width} justifyContent="space-between">
          <Text>
            <Text color={isLive ? 'merged' : bad ? 'warning' : 'success'} bold>{isLive ? spin : bad ? '■' : '✔'} </Text>
            <Text backgroundColor="merged" color="inverseText" bold>{' WORKFLOW '}</Text>
            <Text bold> {cut(w.name, width - 34)}</Text>
          </Text>
          <Text>
            <Text bold color={isLive ? 'merged' : undefined}>{mmss(end - w.startedAt)}</Text>
            <Text color="suggestion"> ~{usd(spent)}</Text>
          </Text>
        </Box>
      )
      const tally = (
        <Text>
          <Text dimColor>{agents.length} ajan · </Text>
          <Text color="success">✔ {done}</Text>
          {bad > 0 && <Text color="error">  ✖ {bad}</Text>}
          {going.length > 0 && <Text color="merged">  ▶ {going.length}</Text>}
        </Text>
      )
      if (!isLive) return [headline, <Text>  {tally}</Text>]
      const total = Math.max(1, agents.length)
      const full = Math.round(((done + bad) / total) * 20)
      const shown = going.slice(0, 5)
      return [
        headline,
        <Text>  <Text color="merged">{'━'.repeat(full)}</Text><Text dimColor>{'─'.repeat(20 - full)}</Text> {tally}</Text>,
        w.phases.length > 0 ? <Text dimColor>  aşamalar: {w.phases.join(' → ')}</Text> : null,
        ...shown.map(r => (
          <Box width={width} justifyContent="space-between">
            <Text>
              {'  '}<Text color="merged">{spin}</Text> <Text dimColor>#{r.workflowIndex}</Text> {cut(r.description || r.subagentType, width - 22)}
            </Text>
            <Text><Text dimColor>{r.tools} araç </Text><Text color="merged">{mmss(now - r.startedAt)}</Text></Text>
          </Box>
        )),
        going.length > shown.length ? <Text dimColor>    … {going.length - shown.length} ajan daha çalışıyor</Text> : null,
        <Text> </Text>,
      ].filter(Boolean)
    })

    // Ended rows (2 each) fill what is left above the pinned footer.
    const used = 2 + 1 + mainCard.length + 1 + flowBlocks.length + (live.length ? 1 + live.length * 6 : 0) + 2 + 4
    const endedFit = Math.max(0, Math.floor((room - used) / 2))

    // Header and runs grow above; the summary and legend stay pinned to the pane's last rows.
    return (
      <Box flexDirection="column" height={rows}>
        <Box flexDirection="column" flexGrow={1} overflow="hidden">
        <Box width={width} justifyContent="space-between">
          <Text><Text bold color="claude">◆ icitech</Text><Text bold> ajanlar</Text></Text>
          <Text>
            <Text color="claude" bold>{live.length ? spin : '▶'} {live.length}</Text>
            {'  '}<Text color="success" bold>✔ {count('done')}</Text>
            {'  '}<Text color="error" bold>✖ {count('failed')}</Text>
            {count('aborted') > 0 && <Text color="warning" bold>{'  '}■ {count('aborted')}</Text>}
          </Text>
        </Box>
        <Text color="claude">{'━'.repeat(width)}</Text>
        <Text> </Text>
        {mainCard}
        <Text> </Text>
        {flowBlocks}
        {list.length === 0 && <Text dimColor>Alt ajan başladığında burada canlı görünür.</Text>}
        {live.length > 0 && [<Text bold color="claude">ÇALIŞIYOR</Text>, ...live.flatMap(liveCard)]}
        {ended.length > 0 && [
          <Text bold color="subtle">BİTENLER</Text>,
          ...ended.slice(0, endedFit).flatMap(endedRow),
          ended.length > endedFit ? <Text dimColor>  … {ended.length - endedFit} eski kayıt</Text> : null,
        ]}
        </Box>
        <Text dimColor>{'─'.repeat(width)}</Text>
        <Text>
          <Text dimColor>Oturum </Text><Text bold>{list.length}</Text><Text dimColor> ajan · </Text>
          <Text bold color="suggestion">{mmss(totalMs)}</Text>
          {longest && <Text dimColor> · en uzun {roleOf(longest).label} {mmss((longest.endedAt ?? now) - longest.startedAt)}</Text>}
        </Text>
        <Text>
          <Text dimColor>Maliyet  ajanlar </Text><Text bold color="suggestion">~{usd(agentsUsd)}</Text>
          {cost && [<Text dimColor> · oturum </Text>, <Text bold color="warning">{usd(cost.usd)}</Text>]}
        </Text>
        <Text dimColor>
          <Text color="suggestion">◇</Text> oku <Text color="claude">✎</Text> yaz <Text color="warning">▸</Text> bash{' '}
          <Text color="suggestion">⌕</Text> ara <Text color="ide">⬡</Text> mcp · /ajanlar kapatır
        </Text>
      </Box>
    )
  })
}
