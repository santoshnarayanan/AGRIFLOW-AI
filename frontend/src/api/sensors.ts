import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { OffsetPaginatedResponse, SensorReading, SensorReadingCreate, SensorType } from '@/types'
import { apiClient } from './client'
import { fetchAllFields, fetchFieldsByFarm } from './fields'

const SENSORS_KEY = ['sensors'] as const

interface SensorReadingApi {
  id: string
  field_id: string
  sensor_type: string
  sensor_value: number
  unit: string
  recorded_at: string
  notes: string | null
  created_at: string
  updated_at: string
}

const SENSOR_TYPE_TO_API: Record<SensorType, string> = {
  soil_moisture: 'SOIL_MOISTURE',
  soil_temperature: 'SOIL_TEMPERATURE',
  air_temperature: 'AIR_TEMPERATURE',
  air_humidity: 'AIR_HUMIDITY',
  light_intensity: 'LIGHT_INTENSITY',
  co2_level: 'AIR_HUMIDITY',
  electrical_conductivity: 'ELECTRICAL_CONDUCTIVITY',
  leaf_wetness: 'LEAF_WETNESS',
}

const API_TO_SENSOR_TYPE: Record<string, SensorType> = {
  SOIL_MOISTURE: 'soil_moisture',
  SOIL_TEMPERATURE: 'soil_temperature',
  AIR_TEMPERATURE: 'air_temperature',
  AIR_HUMIDITY: 'air_humidity',
  LIGHT_INTENSITY: 'light_intensity',
  LEAF_WETNESS: 'leaf_wetness',
  ELECTRICAL_CONDUCTIVITY: 'electrical_conductivity',
  SOIL_SALINITY: 'electrical_conductivity',
  WATER_LEVEL: 'soil_moisture',
  BATTERY_STATUS: 'soil_moisture',
  DEVICE_HEALTH: 'soil_moisture',
}

function mapSensorTypeFromApi(apiType: string): SensorType {
  return API_TO_SENSOR_TYPE[apiType] ?? 'soil_moisture'
}

function mapSensorFromApi(row: SensorReadingApi): SensorReading {
  const sensorType = mapSensorTypeFromApi(row.sensor_type)
  return {
    id: row.id,
    field_id: row.field_id,
    sensor_id: `${row.field_id}-${row.sensor_type}`,
    sensor_type: sensorType,
    value: row.sensor_value,
    unit: row.unit,
    quality_flag: row.notes,
    recorded_at: row.recorded_at,
    created_at: row.created_at,
  }
}

function inDateRange(recordedAt: string, from?: string, to?: string): boolean {
  const day = recordedAt.slice(0, 10)
  if (from && day < from.slice(0, 10)) return false
  if (to && day > to.slice(0, 10)) return false
  return true
}

interface SensorParams {
  fieldIds?: string[]
  fieldId?: string
  farmId?: string
  sensorType?: SensorType
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

async function resolveFieldIds(fieldId?: string, farmId?: string): Promise<string[]> {
  if (fieldId) return [fieldId]
  if (farmId) {
    const fields = await fetchFieldsByFarm(farmId)
    return fields.map((f) => f.id)
  }
  const fields = await fetchAllFields()
  return fields.map((f) => f.id)
}

async function fetchFieldSensors(fieldId: string, limit: number): Promise<SensorReading[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<SensorReadingApi>>(
    `/fields/${fieldId}/sensor-readings`,
    { params: { limit, offset: 0 } },
  )
  return data.items.map(mapSensorFromApi)
}

async function fetchSensorReadings(params: SensorParams = {}): Promise<SensorReading[]> {
  const { sensorType, from, to, limit = 500 } = params
  const fieldIds =
    params.fieldIds?.length
      ? params.fieldIds
      : params.fieldId
        ? [params.fieldId]
        : await resolveFieldIds(undefined, params.farmId)
  if (fieldIds.length === 0) return []

  const perFieldLimit =
    fieldIds.length === 1
      ? limit
      : Math.min(100, Math.max(25, Math.floor(limit / fieldIds.length)))

  const results = await Promise.allSettled(
    fieldIds.map((id) => fetchFieldSensors(id, perFieldLimit)),
  )
  const batches = results
    .filter((r): r is PromiseFulfilledResult<SensorReading[]> => r.status === 'fulfilled')
    .map((r) => r.value)
  if (batches.length === 0 && results.some((r) => r.status === 'rejected')) {
    const first = results.find((r) => r.status === 'rejected') as PromiseRejectedResult
    throw first.reason
  }
  let rows = batches.flat()

  if (sensorType) {
    rows = rows.filter((r) => r.sensor_type === sensorType)
  }
  if (from || to) {
    rows = rows.filter((r) => inDateRange(r.recorded_at, from, to))
  }
  return rows.sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))
}

async function createSensorReading(payload: SensorReadingCreate): Promise<SensorReading> {
  const body = {
    sensor_type: SENSOR_TYPE_TO_API[payload.sensor_type],
    sensor_value: payload.value,
    unit: payload.unit,
    recorded_at: payload.recorded_at,
    ...(payload.quality_flag && { notes: payload.quality_flag }),
  }
  const { data } = await apiClient.post<SensorReadingApi>(
    `/fields/${payload.field_id}/sensor-readings`,
    body,
  )
  return mapSensorFromApi(data)
}

async function deleteSensorReading(id: string): Promise<void> {
  await apiClient.delete(`/sensor-readings/${id}`)
}

export function useSensorReadings(params: SensorParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...SENSORS_KEY, 'v3', queryParams],
    queryFn: () => fetchSensorReadings(queryParams),
    enabled,
  })
}

export function useCreateSensorReading() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSensorReading,
    onSuccess: () => qc.invalidateQueries({ queryKey: SENSORS_KEY }),
  })
}

export function useDeleteSensorReading() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSensorReading,
    onSuccess: () => qc.invalidateQueries({ queryKey: SENSORS_KEY }),
  })
}
