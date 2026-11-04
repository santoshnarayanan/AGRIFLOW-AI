/**
 * Soil types near a location, from ISRIC SoilGrids (free, no API key).
 *
 * SoilGrids returns modelled sand/silt/clay content for any land point at
 * 250 m resolution. To describe the soils "around a city" rather than a
 * single pixel, we sample the centre plus four points ~5 km away (N/E/S/W)
 * across the topsoil layers (0-30 cm) and classify each sample into a USDA
 * texture class.
 *
 * SoilGrids' fair-use limit is ~5 requests/minute per IP, so one lookup is
 * exactly 5 requests and results are cached for the whole session.
 * Urban cores are masked (null values) — the ring of samples covers that.
 */
import { useQuery } from '@tanstack/react-query'
import { usdaTextureClass } from '@/lib/soil'

const SOILGRIDS_URL = 'https://rest.isric.org/soilgrids/v2.0/properties/query'
const RING_OFFSET_DEG = 0.045 // ≈ 5 km in latitude
const DEPTHS = ['0-5cm', '5-15cm', '15-30cm']

interface SoilGridsLayer {
  name: 'sand' | 'silt' | 'clay'
  unit_measure: { d_factor: number }
  depths: { label: string; values: { mean: number | null } }[]
}

async function textureClassesAt(lat: number, lng: number, signal?: AbortSignal): Promise<string[]> {
  const params = new URLSearchParams({ lat: String(lat), lon: String(lng), value: 'mean' })
  for (const p of ['sand', 'silt', 'clay']) params.append('property', p)
  for (const d of DEPTHS) params.append('depth', d)

  const res = await fetch(`${SOILGRIDS_URL}?${params}`, { signal })
  if (!res.ok) throw new Error(`SoilGrids responded ${res.status}`)
  const layers: SoilGridsLayer[] = (await res.json())?.properties?.layers ?? []

  // value / d_factor converts SoilGrids' g/kg integers into percentages.
  const pct = (name: string, depth: string): number | null => {
    const layer = layers.find((l) => l.name === name)
    const mean = layer?.depths.find((d) => d.label === depth)?.values.mean
    return layer && mean != null ? mean / layer.unit_measure.d_factor : null
  }

  const classes: string[] = []
  for (const depth of DEPTHS) {
    const sand = pct('sand', depth)
    const silt = pct('silt', depth)
    const clay = pct('clay', depth)
    if (sand != null && silt != null && clay != null) classes.push(usdaTextureClass(sand, silt, clay))
  }
  return classes
}

/** Distinct USDA texture classes found around (lat, lng), most frequent first. */
export async function fetchSoilTypesNear(lat: number, lng: number, signal?: AbortSignal): Promise<string[]> {
  const lngOffset = RING_OFFSET_DEG / Math.max(Math.cos((lat * Math.PI) / 180), 0.1)
  const points: [number, number][] = [
    [lat, lng],
    [lat + RING_OFFSET_DEG, lng],
    [lat - RING_OFFSET_DEG, lng],
    [lat, lng + lngOffset],
    [lat, lng - lngOffset],
  ]
  const results = await Promise.allSettled(points.map(([a, b]) => textureClassesAt(a, b, signal)))

  const counts = new Map<string, number>()
  let anySucceeded = false
  for (const r of results) {
    if (r.status !== 'fulfilled') continue
    anySucceeded = true
    for (const c of r.value) counts.set(c, (counts.get(c) ?? 0) + 1)
  }
  if (!anySucceeded) throw new Error('Soil lookup failed')
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([c]) => c)
}

/** React Query hook; disabled until a valid location is supplied. */
export function useNearbySoilTypes(lat: number | null, lng: number | null) {
  // Round to ~1 km so nearby farms share a cache entry and we stay under the rate limit.
  const key = lat != null && lng != null ? [Math.round(lat * 100) / 100, Math.round(lng * 100) / 100] : null
  return useQuery({
    queryKey: ['soilgrids', 'texture-classes', key],
    queryFn: ({ signal }) => fetchSoilTypesNear(key![0], key![1], signal),
    enabled: key != null,
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
  })
}
