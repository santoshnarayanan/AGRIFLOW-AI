import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  OffsetPaginatedResponse,
  YieldGrade,
  YieldRecord,
  YieldRecordCreate,
  YieldRecordUpdate,
} from '@/types'
import { apiClient } from './client'

const YIELD_KEY = ['yield'] as const

interface YieldApi {
  id: string
  crop_id: string
  field_id: string
  recorded_at: string
  yield_value_tons_ha: string | number
  measurement_method: string
  area_harvested_ha: string | number | null
  moisture_content_percent: string | number | null
  quality_grade: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

function parseNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function mapGradeFromApi(value: string | null): YieldGrade | null {
  if (!value) return null
  const u = value.toUpperCase()
  if (u.includes('PREMIUM')) return 'premium'
  if (u.includes('GRADE A') || u === 'A') return 'grade_a'
  if (u.includes('GRADE B') || u === 'B') return 'grade_b'
  if (u.includes('GRADE C') || u === 'C') return 'grade_c'
  if (u.includes('REJECT')) return 'reject'
  return 'commercial'
}

function mapGradeToApi(grade: YieldGrade | undefined): string | undefined {
  if (!grade) return undefined
  return GRADE_LABEL[grade]
}

const GRADE_LABEL: Record<YieldGrade, string> = {
  premium: 'Premium',
  grade_a: 'Grade A',
  grade_b: 'Grade B',
  grade_c: 'Grade C',
  commercial: 'Commercial',
  reject: 'Reject',
}

function mapYieldFromApi(row: YieldApi): YieldRecord {
  const yph = parseNum(row.yield_value_tons_ha) ?? 0
  const area = parseNum(row.area_harvested_ha)
  const quantity = area != null && area > 0 ? yph * area : yph
  const unit = area != null && area > 0 ? 't' : 't/ha'
  return {
    id: row.id,
    field_id: row.field_id,
    crop_id: row.crop_id,
    harvest_date: row.recorded_at,
    quantity,
    unit,
    quality_grade: mapGradeFromApi(row.quality_grade),
    moisture_content: parseNum(row.moisture_content_percent),
    area_harvested: area,
    yield_per_hectare: yph,
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

function resolveTonsPerHa(payload: YieldRecordCreate): number {
  if (payload.yield_per_hectare != null && payload.yield_per_hectare > 0) {
    return payload.yield_per_hectare
  }
  if (payload.area_harvested != null && payload.area_harvested > 0) {
    return payload.quantity / payload.area_harvested
  }
  return payload.quantity
}

interface YieldParams {
  fieldId?: string
  fieldIds?: string[]
  cropId?: string
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

async function fetchYieldRecords(params: YieldParams = {}): Promise<YieldRecord[]> {
  const { from, to, limit = 500, fieldId, fieldIds, cropId } = params
  const query: Record<string, unknown> = { limit, offset: 0 }
  if (cropId) {
    query.crop_id = cropId
  } else if (fieldId) {
    query.field_id = fieldId
  } else if (fieldIds && fieldIds.length > 0) {
    query.field_ids = fieldIds
  }

  const { data } = await apiClient.get<OffsetPaginatedResponse<YieldApi>>('/yield-records', {
    params: query,
  })
  let rows = (data.items ?? []).map(mapYieldFromApi)
  if (from || to) {
    rows = rows.filter((r) => inDateRange(r.harvest_date, from, to))
  }
  return rows.sort((a, b) => b.harvest_date.localeCompare(a.harvest_date))
}

function mapCreateToApi(payload: YieldRecordCreate & { crop_id: string }): Record<string, unknown> {
  const harvestIso = payload.harvest_date.includes('T')
    ? payload.harvest_date
    : `${payload.harvest_date}T12:00:00Z`
  return {
    recorded_at: harvestIso,
    yield_value_tons_ha: resolveTonsPerHa(payload),
    measurement_method: 'ESTIMATED',
    area_harvested_ha: payload.area_harvested ?? null,
    moisture_content_percent: payload.moisture_content ?? null,
    quality_grade: mapGradeToApi(payload.quality_grade) ?? null,
    notes: payload.notes ?? null,
  }
}

function mapUpdateToApi(payload: YieldRecordUpdate): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (payload.yield_per_hectare !== undefined) {
    body.yield_value_tons_ha = payload.yield_per_hectare
  } else if (payload.quantity !== undefined) {
    body.yield_value_tons_ha = payload.quantity
  }
  if (payload.moisture_content !== undefined) {
    body.moisture_content_percent = payload.moisture_content
  }
  if (payload.area_harvested !== undefined) body.area_harvested_ha = payload.area_harvested
  if (payload.quality_grade !== undefined) {
    body.quality_grade = payload.quality_grade
      ? mapGradeToApi(payload.quality_grade)
      : null
  }
  if (payload.notes !== undefined) body.notes = payload.notes
  return body
}

async function createYieldRecord(
  payload: YieldRecordCreate & { crop_id: string },
): Promise<YieldRecord> {
  if (!payload.crop_id) {
    throw new Error('A crop is required to log yield.')
  }
  const { data } = await apiClient.post<YieldApi>(
    `/crops/${payload.crop_id}/yield-records`,
    mapCreateToApi(payload),
  )
  return mapYieldFromApi(data)
}

async function updateYieldRecord(id: string, payload: YieldRecordUpdate): Promise<YieldRecord> {
  const { data } = await apiClient.patch<YieldApi>(`/yield-records/${id}`, mapUpdateToApi(payload))
  return mapYieldFromApi(data)
}

async function deleteYieldRecord(id: string): Promise<void> {
  await apiClient.delete(`/yield-records/${id}`)
}

export function useYieldRecords(params: YieldParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...YIELD_KEY, 'v2', queryParams],
    queryFn: () => fetchYieldRecords(queryParams),
    enabled,
    retry: 2,
    refetchOnWindowFocus: false,
  })
}

export function useCreateYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: YieldRecordCreate & { crop_id: string }) => createYieldRecord(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}

export function useUpdateYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: YieldRecordUpdate }) =>
      updateYieldRecord(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}

export function useDeleteYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteYieldRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}
