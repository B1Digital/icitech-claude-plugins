export type Block = {
  startTime: string
  endTime: string
  costUSD: number
  totalTokens: number
  costPerHour: number
  projectedCost: number
  projectedTokens: number
}

export type Month = {
  todayCost: number
  totalCost: number
  totalTokens: number
  activeDays: number
}

export type Day = { date: string; cost: number }

export type Snapshot = {
  user: string
  block: Block | null
  month: Month | null
  calendar: Day[]
  error: string | null
  fetchedAt: number
}

// What this session has cost and which warnings it already gave; reset when the session starts over (/clear).
export type Watch = {
  startedAt: number
  usd: number
  model: string
  budgetStep: number
  opusHinted: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'harcama': { snapshot: Shaped<Snapshot | null>; watch: Shaped<Watch | null> }
  }
}
