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
  on('agent.spawn', () => ({ model: 'claude-opus-5-5', agentId: 'a1' }))
  on('tool.call', () => ({ result: {} }))
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.agent.spawn({ prompt: 'p', description: 'Implement Task 2: token cache', subagentType: 'general-purpose' })
  await $.tool.call({ tool: 'Edit', file_path: '/x/IciSignalNotificationService.cs', old_string: 'a', new_string: 'b', agentId: 'a1' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^ÇALIŞIYOR$/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: / KODLA  #2 token cache/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: /Edit IciSignalNotificationService\.cs/ })) != null).toBe(true)
    await ui.unmount()
  }

  await $.turn.complete({ answer: 'DONE: 3 tests green', durationMs: 1000, isAborted: false, turnId: 't1', agentId: 'a1', reason: 'answer' })

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

  await $.agent.spawn({ prompt: 'p', description: 'Spec review Task 1', subagentType: 'general-purpose' })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /✖  SPEC  #1/ })) != null).toBe(true)
  expect((await ui.find({ type: 'Text', text: /policy says no/ })) != null).toBe(true)
  await ui.unmount()
})
