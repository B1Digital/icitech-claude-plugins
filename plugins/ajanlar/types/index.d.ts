export type RunStatus = 'running' | 'done' | 'failed' | 'aborted'

export type Run = {
  /** Agent tool call id (+ workflow index); stable before the agent id is known. */
  key: string
  agentId: string | null
  parentAgentId: string | null
  description: string
  subagentType: string
  model: string
  background: boolean
  startedAt: number
  endedAt: number | null
  status: RunStatus
  tools: number
  errors: number
  /** Last tool names, oldest first (the coloured strip). */
  recent: string[]
  /** Last tool call, short: "Edit Foo.cs". */
  last: string | null
  /** First line of the answer, or the deny / error reason. */
  note: string | null
}

declare module 'claude-code' {
  interface PluginState {
    'ajanlar': { runs: Shaped<Run[]> }
  }
}
