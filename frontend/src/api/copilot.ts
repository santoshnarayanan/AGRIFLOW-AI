import { apiClient } from './client'

export interface CopilotChatResponse {
  field_id: string
  mode: string
  answer: string
  tools: Array<{ tool: string; result: Record<string, unknown> }>
  mcp_catalog_size: number
}

export async function copilotChat(fieldId: string, message: string): Promise<CopilotChatResponse> {
  const { data } = await apiClient.post<CopilotChatResponse>(
    `/copilot/fields/${fieldId}/chat`,
    { message },
  )
  return data
}
