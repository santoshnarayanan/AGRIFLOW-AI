import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  DiseaseObservation,
  DiseaseObservationCreate,
  DiseaseObservationUpdate,
  DiseaseSeverity,
  OffsetPaginatedResponse,
} from '@/types'
import { apiClient } from './client'

const DISEASE_KEY = ['disease'] as const

interface DiseaseApi {
  id: string
  crop_id: string
  field_id: string
  observed_at: string
  disease_name: string
  severity: string
  affected_area_percent: string | number | null
  diagnosis_method: string
  treatment_applied: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

const SEVERITY_TO_API: Record<DiseaseSeverity, string> = {
  low: 'LOW',
  moderate: 'MEDIUM',
  high: 'HIGH',
  critical: 'CRITICAL',
}

const API_TO_SEVERITY: Record<string, DiseaseSeverity> = {
  LOW: 'low',
  MEDIUM: 'moderate',
  HIGH: 'high',
  CRITICAL: 'critical',
}

function parseNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function mapSeverityFromApi(api: string): DiseaseSeverity {
  return API_TO_SEVERITY[api] ?? 'moderate'
}

function mapDiseaseFromApi(row: DiseaseApi): DiseaseObservation {
  return {
    id: row.id,
    field_id: row.field_id,
    crop_id: row.crop_id,
    disease_name: row.disease_name,
    severity: mapSeverityFromApi(row.severity),
    affected_area_percentage: parseNum(row.affected_area_percent),
    symptoms: null,
    observed_at: row.observed_at,
    treatment_applied: row.treatment_applied,
    treatment_date: null,
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

function buildNotes(payload: {
  symptoms?: string
  treatment_date?: string
  notes?: string
}): string | undefined {
  const parts: string[] = []
  if (payload.symptoms?.trim()) parts.push(`Symptoms: ${payload.symptoms.trim()}`)
  if (payload.treatment_date?.trim()) {
    parts.push(`Treatment date: ${payload.treatment_date.trim()}`)
  }
  if (payload.notes?.trim()) parts.push(payload.notes.trim())
  return parts.length > 0 ? parts.join('\n') : undefined
}

interface DiseaseParams {
  fieldId?: string
  fieldIds?: string[]
  cropId?: string
  severity?: DiseaseSeverity
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

async function fetchFieldDiseaseObservations(
  fieldId: string,
  limit: number,
): Promise<DiseaseObservation[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<DiseaseApi>>(
    `/fields/${fieldId}/disease-observations`,
    { params: { limit, offset: 0 } },
  )
  return (data.items ?? []).map(mapDiseaseFromApi)
}

async function fetchDiseaseObservations(params: DiseaseParams = {}): Promise<DiseaseObservation[]> {
  const { from, to, limit = 500, fieldId, fieldIds, cropId, severity } = params

  let rows: DiseaseObservation[]
  if (fieldId) {
    rows = await fetchFieldDiseaseObservations(fieldId, limit)
  } else if (fieldIds && fieldIds.length > 0) {
    const perField = Math.min(100, Math.max(25, Math.floor(limit / fieldIds.length)))
    const batches = await Promise.all(
      fieldIds.map((id) => fetchFieldDiseaseObservations(id, perField)),
    )
    rows = batches.flat()
  } else if (cropId) {
    const { data } = await apiClient.get<OffsetPaginatedResponse<DiseaseApi>>(
      `/crops/${cropId}/disease-observations`,
      { params: { limit, offset: 0 } },
    )
    rows = (data.items ?? []).map(mapDiseaseFromApi)
  } else {
    rows = []
  }

  if (from || to) {
    rows = rows.filter((r) => inDateRange(r.observed_at, from, to))
  }
  if (severity) {
    rows = rows.filter((r) => r.severity === severity)
  }
  return rows.sort((a, b) => b.observed_at.localeCompare(a.observed_at))
}

function mapCreateToApi(payload: DiseaseObservationCreate): Record<string, unknown> {
  return {
    observed_at: payload.observed_at,
    disease_name: payload.disease_name,
    severity: SEVERITY_TO_API[payload.severity],
    diagnosis_method: 'VISUAL_INSPECTION',
    affected_area_percent: payload.affected_area_percentage ?? null,
    treatment_applied: payload.treatment_applied ?? null,
    notes: buildNotes(payload),
  }
}

function mapUpdateToApi(payload: DiseaseObservationUpdate): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (payload.disease_name !== undefined) body.disease_name = payload.disease_name
  if (payload.severity !== undefined) body.severity = SEVERITY_TO_API[payload.severity]
  if (payload.affected_area_percentage !== undefined) {
    body.affected_area_percent = payload.affected_area_percentage
  }
  if (payload.treatment_applied !== undefined) body.treatment_applied = payload.treatment_applied
  if (
    payload.symptoms !== undefined ||
    payload.treatment_date !== undefined ||
    payload.notes !== undefined
  ) {
    body.notes = buildNotes(payload)
  }
  return body
}

async function createDiseaseObservation(
  payload: DiseaseObservationCreate,
): Promise<DiseaseObservation> {
  const cropId = payload.crop_id
  if (!cropId) {
    throw new Error('A crop cycle is required to log a disease observation.')
  }
  const { data } = await apiClient.post<DiseaseApi>(
    `/crops/${cropId}/disease-observations`,
    mapCreateToApi(payload),
  )
  return mapDiseaseFromApi(data)
}

async function updateDiseaseObservation(
  id: string,
  payload: DiseaseObservationUpdate,
): Promise<DiseaseObservation> {
  const { data } = await apiClient.patch<DiseaseApi>(
    `/disease-observations/${id}`,
    mapUpdateToApi(payload),
  )
  return mapDiseaseFromApi(data)
}

async function deleteDiseaseObservation(id: string): Promise<void> {
  await apiClient.delete(`/disease-observations/${id}`)
}

export function useDiseaseObservations(params: DiseaseParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...DISEASE_KEY, 'v2', queryParams],
    queryFn: () => fetchDiseaseObservations(queryParams),
    enabled,
    retry: 2,
    refetchOnWindowFocus: false,
  })
}

export function useCreateDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createDiseaseObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}

export function useUpdateDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DiseaseObservationUpdate }) =>
      updateDiseaseObservation(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}

export function useDeleteDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteDiseaseObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}
