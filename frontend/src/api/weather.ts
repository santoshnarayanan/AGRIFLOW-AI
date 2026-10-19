import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { OffsetPaginatedResponse, WeatherObservation, WeatherObservationCreate } from '@/types'
import { apiClient } from './client'

const WEATHER_KEY = ['weather'] as const

interface WeatherApi {
  id: string
  field_id: string
  recorded_at: string
  temperature_c: string | number
  humidity_percent: string | number
  rainfall_mm: string | number
  wind_speed_kmh: string | number
  solar_radiation_wm2?: string | number | null
  data_source?: string
  created_at: string
  updated_at: string
}

interface WeatherParams {
  fieldId?: string
  /** When multiple fields (e.g. farm scope), passed as repeated ``field_ids`` query params. */
  fieldIds?: string[]
  from?: string
  to?: string
  limit?: number
  enabled?: boolean
}

function parseNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function mapWeatherFromApi(row: WeatherApi): WeatherObservation {
  return {
    id: row.id,
    field_id: row.field_id,
    temperature: parseNum(row.temperature_c),
    humidity: parseNum(row.humidity_percent),
    rainfall: parseNum(row.rainfall_mm),
    wind_speed: parseNum(row.wind_speed_kmh),
    wind_direction: null,
    solar_radiation: parseNum(row.solar_radiation_wm2 ?? null),
    atmospheric_pressure: null,
    recorded_at: row.recorded_at,
    created_at: row.created_at,
  }
}

function inDateRange(recordedAt: string, from?: string, to?: string): boolean {
  const day = recordedAt.slice(0, 10)
  if (from && day < from) return false
  if (to && day > to) return false
  return true
}

async function fetchWeather(params: WeatherParams = {}): Promise<WeatherObservation[]> {
  const { from, to, limit = 500, fieldId, fieldIds } = params

  const query: Record<string, unknown> = { limit, offset: 0 }
  if (fieldId) {
    query.field_id = fieldId
  } else if (fieldIds && fieldIds.length > 0) {
    query.field_ids = fieldIds
  }

  const { data } = await apiClient.get<OffsetPaginatedResponse<WeatherApi>>('/weather-records', {
    params: query,
  })
  const items = data.items ?? []
  let rows = items.map(mapWeatherFromApi)
  if (from || to) {
    rows = rows.filter((r) => inDateRange(r.recorded_at, from, to))
  }
  return rows.sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))
}

function mapCreateToApi(payload: WeatherObservationCreate): Record<string, unknown> {
  return {
    recorded_at: payload.recorded_at,
    temperature_c: payload.temperature ?? 0,
    humidity_percent: payload.humidity ?? 0,
    rainfall_mm: payload.rainfall ?? 0,
    wind_speed_kmh: payload.wind_speed ?? 0,
    ...(payload.solar_radiation != null && {
      solar_radiation_wm2: payload.solar_radiation,
    }),
    data_source: 'MANUAL',
  }
}

async function createWeatherObservation(
  payload: WeatherObservationCreate,
): Promise<WeatherObservation> {
  const { data } = await apiClient.post<WeatherApi>(
    `/fields/${payload.field_id}/weather-records`,
    mapCreateToApi(payload),
  )
  return mapWeatherFromApi(data)
}

async function deleteWeatherObservation(id: string): Promise<void> {
  await apiClient.delete(`/weather-records/${id}`)
}

export function useWeather(params: WeatherParams = {}) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: [...WEATHER_KEY, 'v4', queryParams],
    queryFn: () => fetchWeather(queryParams),
    enabled,
    retry: 2,
    refetchOnWindowFocus: false,
  })
}

export function useCreateWeather() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createWeatherObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: WEATHER_KEY }),
  })
}

export function useDeleteWeather() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteWeatherObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: WEATHER_KEY }),
  })
}
