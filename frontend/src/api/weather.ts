import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { WeatherObservation, WeatherObservationCreate } from '@/types'
import { apiClient } from './client'

const WEATHER_KEY = ['weather'] as const

interface WeatherParams {
  fieldId?: string
  from?: string
  to?: string
  limit?: number
}

async function fetchWeather(params: WeatherParams = {}): Promise<WeatherObservation[]> {
  const { fieldId, from, to, limit = 200 } = params
  const { data } = await apiClient.get<WeatherObservation[]>('/weather/', {
    params: {
      ...(fieldId && { field_id: fieldId }),
      ...(from && { from }),
      ...(to && { to }),
      limit,
    },
  })
  return data
}

async function createWeatherObservation(
  payload: WeatherObservationCreate,
): Promise<WeatherObservation> {
  const { data } = await apiClient.post<WeatherObservation>('/weather/', payload)
  return data
}

async function deleteWeatherObservation(id: number): Promise<void> {
  await apiClient.delete(`/weather/${id}`)
}

export function useWeather(params: WeatherParams = {}) {
  return useQuery({
    queryKey: [...WEATHER_KEY, params],
    queryFn: () => fetchWeather(params),
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
