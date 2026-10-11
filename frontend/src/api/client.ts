import axios from 'axios'

const eventsOpsKey = import.meta.env.VITE_EVENTS_OPS_API_KEY as string | undefined

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  if (eventsOpsKey && config.url?.includes('/events/outbox')) {
    config.headers.set('X-Events-Ops-Key', eventsOpsKey)
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail ?? err.message ?? 'Request failed'
    return Promise.reject(new Error(message))
  }
)
