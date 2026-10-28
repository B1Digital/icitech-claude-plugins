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
  /** Prompt tokens incl. cache reads/writes, summed over the agent's requests. */
  tokensIn: number
  tokensOut: number
  /** Estimate from list prices; null when the model has no known price. */
  usd: number | null
  /** The Workflow tool call that started this agent's run; null for a plain subagent. */
  workflowId: string | null
  /** The agent's place among its workflow's agent() calls, from 1. */
  workflowIndex: number | null
}

/** The main conversation's own loop (the model talking to the person). */
export type Main = {
  busy: boolean
  /** When the current turn started, or when the last one ended. */
  since: number
  tools: number
  errors: number
  recent: string[]
  last: string | null
  tokensIn: number
  tokensOut: number
  usd: number | null
}

/** A Workflow tool run; its agents point at it by workflowId. */
export type Workflow = {
  id: string
  name: string
  phases: string[]
  startedAt: number
}

declare module 'claude-code' {
  interface PluginState {
    'ajanlar': { runs: Shaped<Run[]>; main: Shaped<Main>; workflows: Shaped<Workflow[]> }
  }
}
