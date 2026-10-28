import { expect, test } from 'claude-code/testing'

const CTX = { windowTokens: 200_000 }

test('bütçe katında ve Opus eşiğinde birer kez uyarır', async ($, on) => {
  const toasts: string[] = []
  on('session.usage', () => ({ value: { startedAt: 1, context: CTX, rateLimits: [] } }))
  on('ui.toast', (_, e) => (toasts.push(e.text), { value: undefined }))
  on('ui.status', () => ({ value: undefined }))
  on('turn.complete', (_, e) => e)
  on('session.measure', (_, e) => ({ changed: e.changed }))

  await $.turn.complete({ turnId: 't1', reason: 'answer', answer: '', durationMs: 1, isAborted: false, text: '', usage: { model: 'claude-opus-5-5' } } as never)
  for (const usd of [4, 11, 12, 16, 17, 31])
    await $.session.measure({ context: CTX, rateLimits: [], cost: { usd }, changed: ['cost'] } as never)

  expect(toasts.filter(t => t.includes('Opus açık')).length).toBe(1)
  expect(toasts.filter(t => t.includes('geçti')).map(t => t.match(/\$(\d+)'i/)?.[1])).toEqual(['15', '30'])
})
