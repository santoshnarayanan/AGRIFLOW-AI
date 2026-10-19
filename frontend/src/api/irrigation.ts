import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  IrrigationEvent,
  IrrigationEventCreate,
  IrrigationEventUpdate,
  IrrigationMethod,
  OffsetPaginatedResponse,
} from '@/types'
import { apiClient } from './client'

const IRRIGATION_KEY = ['irrigation'] as const

interface IrrigationApi {
  id: string
  field_id: string
  started_at: string
  ended_at: string | null
  duration_minutes: string | number | null
  water_volume_liters: string | number | null
  irrigation_method: string
  notes: string | null
  created_at: string
  updated_at: string
}

const METHOD_TO_API: Record<IrrigationMethod, string> = {
  drip: 'DRIP',
  sprinkler: 'SPRINKLER',
  flood: 'FLOOD',
  furrow: 'FURROW',
  center_pivot: 'CENTER_PIVOT',
  subsurface: 'SUBSURFACE',
}

const API_TO_METHOD: Record<string, IrrigationMethod> = {
  DRIP: 'drip',
  SPRINKLER: 'sprinkler',
  FLOOD: 'flood',
  FURROW: 'furrow',
  CENTER_PIVOT: 'center_pivot',
  SUBSURFACE: 'subsurface',
  MANUAL: 'drip',
  AUTOMATED: 'sprinkler',
}

function parseNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function mapMethodFromApi(api: string): IrrigationMethod {
  return API_TO_METHOD[api] ?? 'drip'
}

function mapIrrigationFromApi(row: IrrigationApi): IrrigationEvent {
  return {
    id: row.id,
    field_id: row.field_id,
    crop_id: null,
    start_time: row.started_at,
    end_time: row.ended_at,
    duration_minutes: parseNum(row.duration_minutes),
    water_amount: parseNum(row.water_volume_liters),
    irrigation_method: mapMethodFromApi(row.irrigation_method),
    notes: row.notes,
    created_at: row.created_at,
    updated_at: row.updated_at,
  }
}

function inDateRange(iso: string, from?: string, to?: string): boolean {
  const day = iso.slice(0, 10)
  if (from && day < from.slice(0, 10)) return false
  if (to && day > to.slice(0, 10)) return false
  return true
}

interface IrrigationParams {
  fieldId?: string
  fieldIds?: string[]
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

async function fetchFieldIrrigationEvents(
  fieldId: string,
  limit: number,
): Promise<IrrigationEvent[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<IrrigationApi>>(
    `/fields/${fieldId}/irrigation-events`,
    { params: { limit, offset: 0 } },
  )
  return (data.items ?? []).map(mapIrrigationFromApi)
}

async function fetchIrrigationEvents(params: IrrigationParams = {}): Promise<IrrigationEvent[]> {
  const { from, to, limit = 500, fieldId, fieldIds } = params

  let rows: IrrigationEvent[]
  if (fieldId) {
    rows = await fetchFieldIrrigationEvents(fieldId, limit)
  } else if (fieldIds && fieldIds.length > 0) {
    const perField = Math.min(100, Math.max(25, Math.floor(limit / fieldIds.length)))
    const batches = await Promise.all(
      fieldIds.map((id) => fetchFieldIrrigationEvents(id, perField)),
    )
    rows = batches.flat()
  } else {
    const { data } = await apiClient.get<OffsetPaginatedResponse<IrrigationApi>>(
      '/irrigation-events',
      { params: { limit, offset: 0 } },
    )
    rows = (data.items ?? []).map(mapIrrigationFromApi)
  }

  if (from || to) {
    rows = rows.filter((r) => inDateRange(r.start_time, from, to))
  }
  return rows.sort((a, b) => b.start_time.localeCompare(a.start_time))
}

function mapCreateToApi(payload: IrrigationEventCreate): Record<string, unknown> {
  return {
    started_at: payload.start_time,
    ended_at: payload.end_time ?? null,
    duration_minutes: payload.duration_minutes ?? null,
    water_volume_liters: payload.water_amount ?? null,
    irrigation_method: METHOD_TO_API[payload.irrigation_method],
    notes: payload.notes ?? null,
  }
}

function mapUpdateToApi(payload: IrrigationEventUpdate): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (payload.end_time !== undefined) body.ended_at = payload.end_time
  if (payload.duration_minutes !== undefined) body.duration_minutes = payload.duration_minutes
  if (payload.water_amount !== undefined) body.water_volume_liters = payload.water_amount
  if (payload.irrigation_method !== undefined) {
    body.irrigation_method = METHOD_TO_API[payload.irrigation_method]
  }
  if (payload.notes !== undefined) body.notes = payload.notes
  return body
}

async function createIrrigationEvent(payload: IrrigationEventCreate): Promise<IrrigationEvent> {
  const { data } = await apiClient.post<IrrigationApi>(
    `/fields/${payload.field_id}/irrigation-events`,
    mapCreateToApi(payload),
  )
  return mapIrrigationFromApi(data)
}

async function updateIrrigationEvent(
  id: string,
  payload: IrrigationEventUpdate & { start_time?: string },
): Promise<IrrigationEvent> {
  const body = mapUpdateToApi(payload)
  if (payload.start_time) body.started_at = payload.start_time
  const { data } = await apiClient.patch<IrrigationApi>(`/irrigation-events/${id}`, body)
  return mapIrrigationFromApi(data)
}

async function deleteIrrigationEvent(id: string): Promise<void> {
  await apiClient.delete(`/irrigation-events/${id}`)
}

export function useIrrigationEvents(params: IrrigationParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...IRRIGATION_KEY, 'v3', queryParams],
    queryFn: () => fetchIrrigationEvents(queryParams),
    enabled,
    retry: 2,
    refetchOnWindowFocus: false,
  })
}

export function useCreateIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createIrrigationEvent,
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}

export function useUpdateIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: IrrigationEventUpdate & { start_time?: string } }) =>
      updateIrrigationEvent(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}

export function useDeleteIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteIrrigationEvent,
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}
