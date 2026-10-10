import type { Farm, Field } from '@/types'

/** Human-readable location line for tables and selectors. */
export function formatFarmLocation(farm: Farm): string {
  const parts = [farm.city, farm.state, farm.country].filter(Boolean)
  return parts.length > 0 ? parts.join(', ') : '—'
}

export function farmDisplayName(farm: Farm): string {
  return farm.farm_name
}

export function fieldHasGps(field: Field): boolean {
  return field.latitude != null && field.longitude != null
}

export function formatFieldGps(field: Field): string {
  if (field.latitude == null || field.longitude == null) return '—'
  return `${field.latitude}, ${field.longitude}`
}

export function decimalFromApi(value: string | number | null | undefined): number | null {
  if (value == null || value === '') return null
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : null
}
