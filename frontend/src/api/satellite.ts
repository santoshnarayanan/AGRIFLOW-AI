import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  SatelliteAnalysis,
  SatelliteAnalysisCreate,
  SatelliteAnalysisUpdate,
  SatelliteIndexObservationIds,
  SatelliteSource,
  OffsetPaginatedResponse,
} from '@/types'
import { apiClient } from './client'

const SATELLITE_KEY = ['satellite'] as const

type IndexKey = 'ndvi' | 'ndwi' | 'ndre' | 'evi'

interface SatelliteObservationApi {
  id: string
  field_id: string
  observed_at: string
  satellite_provider: string
  processing_level: string
  spectral_index: string
  index_value: string | number
  cloud_cover_percent: string | number | null
  resolution_m: string | number | null
  scene_id: string | null
  source_url: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

const PROVIDER_TO_API: Record<SatelliteSource, string> = {
  sentinel_2: 'SENTINEL_2',
  landsat_8: 'LANDSAT_8',
  landsat_9: 'LANDSAT_9',
  planet: 'PLANET',
  modis: 'MODIS',
  spot: 'SPOT',
}

const API_TO_PROVIDER: Record<string, SatelliteSource> = {
  SENTINEL_2: 'sentinel_2',
  LANDSAT_8: 'landsat_8',
  LANDSAT_9: 'landsat_9',
  PLANET: 'planet',
  MODIS: 'modis',
  SPOT: 'spot',
  WORLDVIEW: 'planet',
  UNKNOWN: 'sentinel_2',
}

const INDEX_TO_KEY: Record<string, IndexKey> = {
  NDVI: 'ndvi',
  NDWI: 'ndwi',
  NDRE: 'ndre',
  EVI: 'evi',
}

const KEY_TO_INDEX: Record<IndexKey, string> = {
  ndvi: 'NDVI',
  ndwi: 'NDWI',
  ndre: 'NDRE',
  evi: 'EVI',
}

function parseNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function mapProviderFromApi(api: string): SatelliteSource | null {
  return API_TO_PROVIDER[api] ?? null
}

function toIsoRangeStart(day: string): string {
  return day.includes('T') ? day : `${day}T00:00:00Z`
}

function toIsoRangeEnd(day: string): string {
  return day.includes('T') ? day : `${day}T23:59:59Z`
}

function groupKey(row: SatelliteObservationApi): string {
  return `${row.field_id}|${row.observed_at}`
}

function pivotObservations(rows: SatelliteObservationApi[]): SatelliteAnalysis[] {
  const groups = new Map<
    string,
    SatelliteAnalysis & { observation_ids: SatelliteIndexObservationIds }
  >()

  for (const row of rows) {
    const key = groupKey(row)
    let group = groups.get(key)
    if (!group) {
      group = {
        id: row.id,
        field_id: row.field_id,
        acquisition_date: row.observed_at,
        satellite_source: mapProviderFromApi(row.satellite_provider),
        cloud_cover_percentage: parseNum(row.cloud_cover_percent),
        ndvi: null,
        ndwi: null,
        ndre: null,
        evi: null,
        image_url: row.source_url,
        notes: row.notes,
        created_at: row.created_at,
        updated_at: row.updated_at,
        observation_ids: {},
      }
      groups.set(key, group)
    }

    const indexKey = INDEX_TO_KEY[row.spectral_index]
    if (indexKey) {
      group[indexKey] = parseNum(row.index_value)
      group.observation_ids[indexKey] = row.id
      if (indexKey === 'ndvi') group.id = row.id
    }

    if (row.cloud_cover_percent != null) {
      group.cloud_cover_percentage = parseNum(row.cloud_cover_percent)
    }
    if (row.source_url) group.image_url = row.source_url
    if (row.updated_at > group.updated_at) group.updated_at = row.updated_at
  }

  return Array.from(groups.values()).sort((a, b) =>
    b.acquisition_date.localeCompare(a.acquisition_date),
  )
}

interface SatelliteParams {
  fieldId?: string
  fieldIds?: string[]
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

async function fetchFieldSatelliteRows(
  fieldId: string,
  limit: number,
  from?: string,
  to?: string,
): Promise<SatelliteObservationApi[]> {
  if (from && to) {
    const { data } = await apiClient.get<OffsetPaginatedResponse<SatelliteObservationApi>>(
      `/fields/${fieldId}/satellite-observations/range`,
      {
        params: {
          start: toIsoRangeStart(from),
          end: toIsoRangeEnd(to),
          limit,
          offset: 0,
        },
      },
    )
    return data.items ?? []
  }

  const { data } = await apiClient.get<OffsetPaginatedResponse<SatelliteObservationApi>>(
    `/fields/${fieldId}/satellite-observations`,
    { params: { limit, offset: 0 } },
  )
  return data.items ?? []
}

async function fetchSatelliteAnalyses(params: SatelliteParams = {}): Promise<SatelliteAnalysis[]> {
  const { from, to, limit = 500, fieldId, fieldIds } = params

  let rows: SatelliteObservationApi[]
  if (fieldId) {
    rows = await fetchFieldSatelliteRows(fieldId, limit, from, to)
  } else if (fieldIds && fieldIds.length > 0) {
    const perField = Math.min(200, Math.max(50, Math.floor(limit / fieldIds.length)))
    const batches = await Promise.all(
      fieldIds.map((id) => fetchFieldSatelliteRows(id, perField, from, to)),
    )
    rows = batches.flat()
  } else {
    rows = []
  }

  return pivotObservations(rows)
}

function buildCreateBody(
  payload: SatelliteAnalysisCreate,
  spectralIndex: string,
  indexValue: number,
): Record<string, unknown> {
  return {
    observed_at: payload.acquisition_date.includes('T')
      ? payload.acquisition_date
      : `${payload.acquisition_date}T12:00:00Z`,
    satellite_provider: payload.satellite_source
      ? PROVIDER_TO_API[payload.satellite_source]
      : 'SENTINEL_2',
    processing_level: 'L2A',
    spectral_index: spectralIndex,
    index_value: indexValue,
    cloud_cover_percent: payload.cloud_cover_percentage ?? null,
    source_url: payload.image_url ?? null,
    notes: payload.notes ?? null,
  }
}

function indexEntries(
  payload: SatelliteAnalysisCreate | SatelliteAnalysisUpdate,
): Array<[IndexKey, number]> {
  const keys: IndexKey[] = ['ndvi', 'ndwi', 'ndre', 'evi']
  return keys
    .map((key) => [key, payload[key] as number | undefined])
    .filter((entry): entry is [IndexKey, number] => entry[1] != null && Number.isFinite(entry[1]))
}

async function createSatelliteAnalysis(
  payload: SatelliteAnalysisCreate,
): Promise<SatelliteAnalysis> {
  const entries = indexEntries(payload)
  if (entries.length === 0) {
    throw new Error('Enter at least one vegetation index value (e.g. NDVI).')
  }

  const created: SatelliteObservationApi[] = []
  for (const [key, value] of entries) {
    const { data } = await apiClient.post<SatelliteObservationApi>(
      `/fields/${payload.field_id}/satellite-observations`,
      buildCreateBody(payload, KEY_TO_INDEX[key], value),
    )
    created.push(data)
  }
  const [analysis] = pivotObservations(created)
  if (!analysis) throw new Error('Failed to create satellite observation.')
  return analysis
}

async function updateSatelliteAnalysis(
  analysis: SatelliteAnalysis,
  payload: SatelliteAnalysisUpdate,
): Promise<SatelliteAnalysis> {
  const ids = analysis.observation_ids ?? {}
  const sharedPatch: Record<string, unknown> = {}
  if (payload.satellite_source !== undefined) {
    sharedPatch.satellite_provider = PROVIDER_TO_API[payload.satellite_source]
  }
  if (payload.cloud_cover_percentage !== undefined) {
    sharedPatch.cloud_cover_percent = payload.cloud_cover_percentage
  }
  if (payload.image_url !== undefined) sharedPatch.source_url = payload.image_url
  if (payload.notes !== undefined) sharedPatch.notes = payload.notes

  const updatedRows: SatelliteObservationApi[] = []

  for (const [key, value] of indexEntries(payload)) {
    const observationId = ids[key]
    const body = { ...sharedPatch, index_value: value }
    if (observationId) {
      const { data } = await apiClient.patch<SatelliteObservationApi>(
        `/satellite-observations/${observationId}`,
        body,
      )
      updatedRows.push(data)
    }
  }

  if (updatedRows.length === 0 && Object.keys(sharedPatch).length > 0) {
    const fallbackId = analysis.id
    const { data } = await apiClient.patch<SatelliteObservationApi>(
      `/satellite-observations/${fallbackId}`,
      sharedPatch,
    )
    updatedRows.push(data)
  }

  if (updatedRows.length === 0) return analysis
  const [merged] = pivotObservations(updatedRows)
  return merged ?? analysis
}

async function deleteSatelliteAnalysis(analysis: SatelliteAnalysis): Promise<void> {
  const ids = new Set<string>(
    Object.values(analysis.observation_ids ?? {}).filter(Boolean) as string[],
  )
  if (ids.size === 0) ids.add(analysis.id)
  await Promise.all([...ids].map((id) => apiClient.delete(`/satellite-observations/${id}`)))
}

export function useSatelliteAnalyses(params: SatelliteParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...SATELLITE_KEY, 'v2', queryParams],
    queryFn: () => fetchSatelliteAnalyses(queryParams),
    enabled,
    retry: 2,
    refetchOnWindowFocus: false,
  })
}

export function useCreateSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSatelliteAnalysis,
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}

export function useUpdateSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      analysis,
      payload,
    }: {
      analysis: SatelliteAnalysis
      payload: SatelliteAnalysisUpdate
    }) => updateSatelliteAnalysis(analysis, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}

export function useDeleteSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSatelliteAnalysis,
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}
