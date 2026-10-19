import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Crop, CropCreate, CropStatus, CropUpdate, GrowthStage, OffsetPaginatedResponse } from '@/types'
import { apiClient } from './client'
import { fetchFarms } from '@/api/farms'

const CROPS_KEY = ['crops'] as const

/** Wire format from FastAPI ``CropResponse`` (``crop_name`` / ``crop_variety``). */
interface CropApi {
  id: string
  field_id: string
  crop_name: string
  crop_variety: string | null
  growth_stage: string | null
  planting_date: string
  expected_harvest_date: string | null
  actual_harvest_date: string | null
  status: string
  created_at: string
  updated_at: string
}

function mapCropStatus(apiStatus: string): CropStatus {
  switch (apiStatus.toUpperCase()) {
    case 'PLANNED':
      return 'planned'
    case 'PLANTED':
    case 'GROWING':
      return 'active'
    case 'HARVESTED':
      return 'harvested'
    default:
      return 'planned'
  }
}

function mapStatusToApi(status: CropStatus): string {
  switch (status) {
    case 'planned':
      return 'PLANNED'
    case 'active':
      return 'GROWING'
    case 'harvested':
      return 'HARVESTED'
    case 'failed':
      return 'HARVESTED'
    default:
      return 'PLANNED'
  }
}

function mapGrowthStageFromApi(value: string | null): GrowthStage {
  if (!value) return 'vegetative'
  const normalized = value.toLowerCase()
  const known: GrowthStage[] = [
    'seedling',
    'vegetative',
    'flowering',
    'fruiting',
    'ripening',
    'harvested',
  ]
  if (known.includes(normalized as GrowthStage)) {
    return normalized as GrowthStage
  }
  if (value.toUpperCase().startsWith('BBCH')) {
    return 'harvested'
  }
  return 'vegetative'
}

export function mapCropFromApi(row: CropApi): Crop {
  return {
    id: row.id,
    field_id: row.field_id,
    name: row.crop_name,
    variety: row.crop_variety,
    growth_stage: mapGrowthStageFromApi(row.growth_stage),
    growth_stage_label: row.growth_stage,
    planting_date: row.planting_date,
    expected_harvest_date: row.expected_harvest_date,
    actual_harvest_date: row.actual_harvest_date,
    status: mapCropStatus(row.status),
    created_at: row.created_at,
    updated_at: row.updated_at,
  }
}

function mapCropCreateToApi(payload: CropCreate): Record<string, unknown> {
  const body: Record<string, unknown> = {
    crop_name: payload.name,
    crop_variety: payload.variety ?? null,
  }
  if (payload.planting_date) body.planting_date = payload.planting_date
  if (payload.expected_harvest_date) body.expected_harvest_date = payload.expected_harvest_date
  if (payload.growth_stage) body.growth_stage = payload.growth_stage
  if (payload.status) body.status = mapStatusToApi(payload.status)
  return body
}

function mapCropUpdateToApi(payload: CropUpdate): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (payload.name !== undefined) body.crop_name = payload.name
  if (payload.variety !== undefined) body.crop_variety = payload.variety
  if (payload.planting_date !== undefined) body.planting_date = payload.planting_date
  if (payload.expected_harvest_date !== undefined) {
    body.expected_harvest_date = payload.expected_harvest_date
  }
  if (payload.actual_harvest_date !== undefined) {
    body.actual_harvest_date = payload.actual_harvest_date
  }
  if (payload.growth_stage !== undefined) body.growth_stage = payload.growth_stage
  if (payload.status !== undefined) body.status = mapStatusToApi(payload.status)
  return body
}

async function fetchCropsByField(fieldId: string): Promise<Crop[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<CropApi>>(
    `/fields/${fieldId}/crops`,
    { params: { limit: 500, offset: 0 } },
  )
  return data.items.map(mapCropFromApi)
}

async function fetchAllCrops(): Promise<Crop[]> {
  const farms = await fetchFarms()
  const fieldBatches = await Promise.all(
    farms.map(async (farm) => {
      const { data } = await apiClient.get<OffsetPaginatedResponse<{ id: string }>>(
        `/farms/${farm.id}/fields`,
        { params: { limit: 500, offset: 0 } },
      )
      return data.items
    }),
  )
  const fieldIds = fieldBatches.flat().map((f) => f.id)
  if (fieldIds.length === 0) return []
  const cropBatches = await Promise.all(fieldIds.map((id) => fetchCropsByField(id)))
  return cropBatches.flat()
}

async function fetchCrop(id: string): Promise<Crop> {
  const { data } = await apiClient.get<CropApi>(`/crops/${id}`)
  return mapCropFromApi(data)
}

async function createCrop(fieldId: string, payload: CropCreate): Promise<Crop> {
  const { data } = await apiClient.post<CropApi>(
    `/fields/${fieldId}/crops`,
    mapCropCreateToApi(payload),
  )
  return mapCropFromApi(data)
}

async function updateCrop(id: string, payload: CropUpdate): Promise<Crop> {
  const { data } = await apiClient.patch<CropApi>(`/crops/${id}`, mapCropUpdateToApi(payload))
  return mapCropFromApi(data)
}

async function deleteCrop(id: string): Promise<void> {
  await apiClient.delete(`/crops/${id}`)
}

/** Normalize rows whether they came from the API or an older React Query cache. */
export function normalizeCropRow(row: Crop | CropApi): Crop {
  if ('crop_name' in row && row.crop_name) {
    return mapCropFromApi(row as CropApi)
  }
  return row as Crop
}

export function useCrops(fieldId?: string) {
  return useQuery({
    queryKey: fieldId ? [...CROPS_KEY, 'v2', 'field', fieldId] : [...CROPS_KEY, 'v2', 'all'],
    queryFn: async () => {
      const rows = fieldId ? await fetchCropsByField(fieldId) : await fetchAllCrops()
      return rows.map((row) => normalizeCropRow(row))
    },
  })
}

export function useCrop(id: string) {
  return useQuery({
    queryKey: [...CROPS_KEY, id],
    queryFn: () => fetchCrop(id),
    enabled: !!id,
  })
}

export function useCreateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ fieldId, payload }: { fieldId: string; payload: CropCreate }) =>
      createCrop(fieldId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}

export function useUpdateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CropUpdate }) =>
      updateCrop(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}

export function useDeleteCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteCrop,
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}
