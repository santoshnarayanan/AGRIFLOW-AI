import axios from 'axios'
import { getStoredAccessToken } from '@/stores/authStore'

const eventsOpsKey = import.meta.env.VITE_EVENTS_OPS_API_KEY as string | undefined

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  // Local CDD/demo stacks can be slow (many fields × weather rows); avoid false "backend down" errors.
  timeout: 180_000,
  // FastAPI repeated query params: field_ids=a&field_ids=b (not field_ids[]=a)
  paramsSerializer: { indexes: null },
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredAccessToken()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
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
