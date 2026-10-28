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

// Limit pencereleri (kind@resetsAt) için verilmiş uyarılar; pencere yenilenince anahtar değişir, uyarı yeniden verilir.
export type Warned = string[]

declare module 'claude-code' {
  interface PluginState {
    'harcama': { snapshot: Shaped<Snapshot | null>; warned: Shaped<Warned> }
  }
}
