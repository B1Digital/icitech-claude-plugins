import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'ajanlar',
  component: 'Pane',
  requestId: 'agents',
  props: {
    title: 'Ajanlar',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

test('an implementer run shows live, then ends with its result', async ($, on) => {
  // These hooks stand for the engine beneath the plugin.
  on('command.register', () => ({ value: { command: 'ajanlar' } }))
  on('ui.panes', () => ({ value: [] }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('clock.every', () => ({ value: () => {} }))
  on('agent.list', () => ({ value: [] }))
  on('store.get', () => ({ value: undefined }))
  on('store.set', () => ({ value: undefined }))
  // LiteLLM list says $8 in / $40 out for opus-5-5 here, so the estimate must come from the list, not the table.
  on('http.fetch', () => ({ value: { status: 200, ok: true, headers: {}, text: JSON.stringify({ 'claude-opus-5-5': { input_cost_per_token: 8e-6, output_cost_per_token: 4e-5, cache_read_input_token_cost: 4e-7, cache_creation_input_token_cost: 1e-5 } }) } }))
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [], cost: { usd: 1.5 } } }))
  on('agent.spawn', () => ({ model: 'claude-opus-5-5', agentId: 'a1' }))
  on('tool.call', () => ({ result: {} }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('turn.step', async function* (_, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: { model: 'claude-opus-5-5', input_tokens: 1000, output_tokens: 300, cache_read_input_tokens: 200, cache_creation_input_tokens: 0 } }
  })

  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.agent.spawn({ prompt: 'p', description: 'Implement Task 2: token cache', subagentType: 'general-purpose' })
  // One opus-5-5 request at list prices: (1000·8 + 200·0.4 + 300·40) / 1e6 = $0.02008
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-opus-5-5', messageCount: 1, agentId: 'a1' })) { /* drain */ }
  await $.tool.call({ tool: 'Edit', file_path: '/x/IciSignalNotificationService.cs', old_string: 'a', new_string: 'b', agentId: 'a1' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^ÇALIŞIYOR$/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: / KODLA  #2 token cache/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: /Edit IciSignalNotificationService\.cs/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: /↑1\.2k ↓300 ~\$0\.02/ })) != null).toBe(true)
    await ui.unmount()
  }

  await $.turn.complete({ answer: '\n### **DONE**: 3 tests `green`', durationMs: 1000, isAborted: false, turnId: 't1', agentId: 'a1', reason: 'answer' })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /^ÇALIŞIYOR$/ })) == null).toBe(true)
  expect((await ui.find({ type: 'Text', text: /^BİTENLER$/ })) != null).toBe(true)
  expect((await ui.find({ type: 'Text', text: /DONE: 3 tests green/ })) != null).toBe(true)
  await ui.unmount()
})

test('a denied spawn is listed as failed with the reason', async ($, on) => {
  on('ui.panes', () => ({ value: [] }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('agent.spawn', () => ({ deny: 'policy says no' }))
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [], cost: { usd: 0 } } }))

  await $.agent.spawn({ prompt: 'p', description: 'Spec review Task 1', subagentType: 'general-purpose' })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /✖  SPEC  #1/ })) != null).toBe(true)
  expect((await ui.find({ type: 'Text', text: /policy says no/ })) != null).toBe(true)
  await ui.unmount()
})
