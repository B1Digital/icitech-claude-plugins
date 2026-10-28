import { atom, read, update } from 'claude-code'
import type { Color, EngineInterface, Register } from 'claude-code'

import type { Run, RunStatus } from '../types'

const PANE = 'agents'
const TITLE = 'Ajanlar'
const KEEP = 40
const STRIP = 18

const runs = atom({ plugin: 'ajanlar', key: 'runs' } as const, [], { shape: 'runs-1' })

const isOpen = async ($: EngineInterface) =>
  (await $.ui.panes()).some(pane => pane.id === PANE)

// Redraw ticks only while something runs; module state is rebuilt on reload, which only pauses the spinner.
let running = 0
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
      if (running > 0) $.ui.invalidate('ui.render')
    })
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
    }
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
    if (!id) return next(e)
    const last = detail(e.tool, e as unknown as Record<string, unknown>)
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

  on('turn.complete', async ($, e, next) => {
    const id = e.agentId
    if (id) {
      const status: RunStatus = e.isAborted ? 'aborted' : e.reason === 'answer' ? 'done' : 'failed'
      const note = cut((e.answer ?? '').split('\n').find(l => l.trim()) ?? '', 90) || null
      await patch($, r => r.agentId === id && r.status === 'running', r => ({ ...r, status, endedAt: Date.now(), note }))
    }
    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, runs)
    const now = Date.now()
    const width = Math.max(30, Math.min(64, (e.viewport?.columns ?? 60) - 2))
    const room = Math.max(8, (e.viewport?.rows ?? 30) - 2)
    const spin = SPIN[Math.floor(now / 100) % SPIN.length]

    const live = list.filter(r => r.status === 'running')
    const ended = list.filter(r => r.status !== 'running').sort((a, b) => (b.endedAt ?? 0) - (a.endedAt ?? 0))
    const count = (s: RunStatus) => list.filter(r => r.status === s).length
    const totalMs = list.reduce((sum, r) => sum + ((r.endedAt ?? now) - r.startedAt), 0)
    const longest = list.reduce<Run | null>((best, r) => {
      const ms = (r.endedAt ?? now) - r.startedAt
      return !best || ms > (best.endedAt ?? now) - best.startedAt ? r : best
    }, null)

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
          : <Text>{indent(r)}  <Text dimColor>{r.tools} araç{r.note ? ` · ${cut(r.note, width - 16)}` : ''}</Text></Text>,
      ]
    }

    // Live cards take 5 rows each, ended rows 2; ended rows fill what is left.
    const used = 6 + live.length * 5 + (live.length ? 1 : 0) + 4
    const endedFit = Math.max(0, Math.floor((room - used) / 2))

    return (
      <Box flexDirection="column">
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
        {list.length === 0 && [
          <Text> </Text>,
          <Text dimColor>Henüz ajan çalışmadı.</Text>,
          <Text dimColor>Bir alt ajan başladığında burada canlı görünür.</Text>,
        ]}
        {live.length > 0 && [<Text> </Text>, <Text bold color="claude">ÇALIŞIYOR</Text>, ...live.flatMap(liveCard)]}
        {ended.length > 0 && [
          <Text bold color="subtle">BİTENLER</Text>,
          ...ended.slice(0, endedFit).flatMap(endedRow),
          ended.length > endedFit ? <Text dimColor>  … {ended.length - endedFit} eski kayıt</Text> : null,
        ]}
        {list.length > 0 && [
          <Text dimColor>{'─'.repeat(width)}</Text>,
          <Text>
            <Text dimColor>Oturum </Text><Text bold>{list.length}</Text><Text dimColor> ajan · toplam </Text>
            <Text bold color="suggestion">{mmss(totalMs)}</Text>
            {longest && <Text dimColor> · en uzun {roleOf(longest).label.toLowerCase()} {mmss((longest.endedAt ?? now) - longest.startedAt)}</Text>}
          </Text>,
        ]}
        <Text dimColor>
          <Text color="suggestion">◇</Text> oku <Text color="claude">✎</Text> yaz <Text color="warning">▸</Text> bash{' '}
          <Text color="suggestion">⌕</Text> ara <Text color="ide">⬡</Text> mcp · /ajanlar kapatır
        </Text>
      </Box>
    )
  })
}
