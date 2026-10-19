import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { SoilProfile, SoilProfileCreate, SoilProfileUpdate, SoilTexture } from '@/types'
import { apiClient } from './client'

const SOIL_KEY = ['soil-profiles'] as const

interface SoilProfileApi {
  id: string
  field_id: string
  soil_type: string
  ph: string | null
  organic_matter: string | null
  nitrogen: string | null
  phosphorus: string | null
  potassium: string | null
  soil_depth_cm: string | null
  cation_exchange_capacity_meq: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

const SOIL_TYPE_TO_TEXTURE: Record<string, SoilTexture> = {
  SANDY: 'sandy',
  CLAY: 'clay',
  LOAM: 'loam',
  SILT: 'silt_loam',
  PEAT: 'peat',
  CHALK: 'loam',
}

const TEXTURE_TO_SOIL_TYPE: Record<SoilTexture, string> = {
  sandy: 'SANDY',
  sandy_loam: 'LOAM',
  loam: 'LOAM',
  silt_loam: 'SILT',
  silt: 'SILT',
  clay_loam: 'CLAY',
  clay: 'CLAY',
  peat: 'PEAT',
}

function parseNum(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

export function mapSoilProfileFromApi(row: SoilProfileApi): SoilProfile {
  const soilType = row.soil_type?.toUpperCase() ?? 'LOAM'
  return {
    id: row.id,
    field_id: row.field_id,
    ph_level: parseNum(row.ph),
    nitrogen_content: parseNum(row.nitrogen),
    phosphorus_content: parseNum(row.phosphorus),
    potassium_content: parseNum(row.potassium),
    organic_matter: parseNum(row.organic_matter),
    moisture_content: null,
    texture: SOIL_TYPE_TO_TEXTURE[soilType] ?? 'loam',
    notes: row.notes,
    recorded_at: row.created_at,
    created_at: row.created_at,
    updated_at: row.updated_at,
  }
}

function mapCreateToApi(payload: SoilProfileCreate): Record<string, unknown> {
  const texture = payload.texture ?? 'loam'
  return {
    soil_type: TEXTURE_TO_SOIL_TYPE[texture] ?? 'LOAM',
    ph: payload.ph_level ?? null,
    nitrogen: payload.nitrogen_content ?? null,
    phosphorus: payload.phosphorus_content ?? null,
    potassium: payload.potassium_content ?? null,
    organic_matter: payload.organic_matter ?? null,
    notes: payload.notes ?? null,
  }
}

function mapUpdateToApi(payload: SoilProfileUpdate): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (payload.texture !== undefined) {
    body.soil_type = TEXTURE_TO_SOIL_TYPE[payload.texture] ?? 'LOAM'
  }
  if (payload.ph_level !== undefined) body.ph = payload.ph_level
  if (payload.nitrogen_content !== undefined) body.nitrogen = payload.nitrogen_content
  if (payload.phosphorus_content !== undefined) body.phosphorus = payload.phosphorus_content
  if (payload.potassium_content !== undefined) body.potassium = payload.potassium_content
  if (payload.organic_matter !== undefined) body.organic_matter = payload.organic_matter
  if (payload.notes !== undefined) body.notes = payload.notes
  return body
}

async function fetchSoilProfiles(fieldId?: string): Promise<SoilProfile[]> {
  const params: Record<string, string | number> = { limit: 500, offset: 0 }
  if (fieldId) params.field_id = fieldId
  const { data } = await apiClient.get<SoilProfileApi[]>('/soil-profiles', { params })
  return data.map(mapSoilProfileFromApi)
}

async function createSoilProfile(payload: SoilProfileCreate): Promise<SoilProfile> {
  const { data } = await apiClient.post<SoilProfileApi>(
    `/fields/${payload.field_id}/soil-profile`,
    mapCreateToApi(payload),
  )
  return mapSoilProfileFromApi(data)
}

async function updateSoilProfile(id: string, payload: SoilProfileUpdate): Promise<SoilProfile> {
  const { data } = await apiClient.patch<SoilProfileApi>(`/soil-profiles/${id}`, mapUpdateToApi(payload))
  return mapSoilProfileFromApi(data)
}

async function deleteSoilProfile(id: string): Promise<void> {
  await apiClient.delete(`/soil-profiles/${id}`)
}

export function useSoilProfiles(fieldId?: string) {
  return useQuery({
    queryKey: fieldId ? [...SOIL_KEY, 'v3', 'field', fieldId] : [...SOIL_KEY, 'v3', 'all'],
    queryFn: () => fetchSoilProfiles(fieldId),
    retry: 1,
  })
}

export function useCreateSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSoilProfile,
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}

export function useUpdateSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SoilProfileUpdate }) =>
      updateSoilProfile(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}

export function useDeleteSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSoilProfile,
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}
