import { expect, test } from 'claude-code/testing'

const CTX = { windowTokens: 200_000 }
const lim = (kind: string, percentUsed: number, resetsAt: string) => ({ kind, percentUsed, resetsAt, source: 'api' })

test('her limit penceresinde eşik bir kez uyarılır, yeni pencerede tekrar', async ($, on) => {
  const toasts: string[] = []
  on('ui.toast', (_, e) => (toasts.push(e.text), { value: undefined }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  const measure = (rateLimits: ReturnType<typeof lim>[]) =>
    $.session.measure({ context: CTX, rateLimits, changed: ['rateLimits'] } as never)

  await measure([lim('five_hour', 50, '2026-10-28T20:00:00Z'), lim('seven_day', 70, '2026-11-02T10:00:00Z')])
  await measure([lim('five_hour', 81, '2026-10-28T20:00:00Z'), lim('seven_day', 79, '2026-11-02T10:00:00Z')])
  await measure([lim('five_hour', 90, '2026-10-28T20:00:00Z'), lim('seven_day', 85, '2026-11-02T10:00:00Z')])
  await measure([lim('five_hour', 82, '2026-10-29T01:00:00Z')])

  expect(toasts.map(t => t.split(' ')[0])).toEqual(['5', 'Haftalık', '5'])
})
