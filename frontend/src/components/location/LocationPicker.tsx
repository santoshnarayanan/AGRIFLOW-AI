import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Crosshair, Loader2, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export interface PickedAddress {
  city?: string
  state?: string
  country?: string
}

interface LocationPickerProps {
  latitude: string
  longitude: string
  /** Called when the user picks a point (click, drag, search, or geolocation). */
  onPick: (lat: number, lng: number) => void
  /** Called once reverse geocoding resolves for a picked point. */
  onAddress?: (address: PickedAddress) => void
  /** Where to centre the map while no point is set (e.g. the parent farm). */
  defaultCenter?: [number, number] | null
}

const NOMINATIM = 'https://nominatim.openstreetmap.org'
const DEFAULT_CENTER: L.LatLngTuple = [20, 0]

const pinIcon = L.divIcon({
  className: '',
  html: `<svg width="28" height="40" viewBox="0 0 28 40" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.3 21.7 0 14 0z" fill="#16a34a" stroke="#fff" stroke-width="2"/>
    <circle cx="14" cy="14" r="5" fill="#fff"/></svg>`,
  iconSize: [28, 40],
  iconAnchor: [14, 40],
})

const round6 = (n: number) => Math.round(n * 1e6) / 1e6

function parseCoord(lat: string, lng: string): L.LatLngTuple | null {
  const a = Number(lat)
  const b = Number(lng)
  if (lat === '' || lng === '' || isNaN(a) || isNaN(b)) return null
  if (a < -90 || a > 90 || b < -180 || b > 180) return null
  return [a, b]
}

async function reverseGeocode(lat: number, lng: number): Promise<PickedAddress | null> {
  try {
    const res = await fetch(`${NOMINATIM}/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`)
    if (!res.ok) return null
    const data = await res.json()
    const a = data?.address ?? {}
    return {
      city: a.city || a.town || a.village || a.hamlet || a.municipality || a.county,
      state: a.state || a.region || a.state_district,
      country: a.country,
    }
  } catch {
    return null
  }
}

export function LocationPicker({ latitude, longitude, onPick, onAddress, defaultCenter }: LocationPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)
  const onPickRef = useRef(onPick)
  const onAddressRef = useRef(onAddress)
  onPickRef.current = onPick
  onAddressRef.current = onAddress

  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [locating, setLocating] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  // Shared handler for every way of choosing a point.
  const pickRef = useRef<(lat: number, lng: number, zoom?: number) => void>(() => {})
  pickRef.current = (lat, lng, zoom) => {
    const map = mapRef.current
    if (!map) return
    const ll: L.LatLngTuple = [round6(lat), round6(L.Util.wrapNum(lng, [-180, 180], true))]
    placeMarker(ll)
    if (zoom) map.setView(ll, zoom)
    onPickRef.current(ll[0], ll[1])
    if (onAddressRef.current) {
      reverseGeocode(ll[0], ll[1]).then((addr) => addr && onAddressRef.current?.(addr))
    }
  }

  function placeMarker(ll: L.LatLngTuple) {
    const map = mapRef.current
    if (!map) return
    if (markerRef.current) {
      markerRef.current.setLatLng(ll)
      return
    }
    const marker = L.marker(ll, { icon: pinIcon, draggable: true }).addTo(map)
    marker.on('dragend', () => {
      const p = marker.getLatLng()
      pickRef.current(p.lat, p.lng)
    })
    markerRef.current = marker
  }

  // Create the map once.
  useEffect(() => {
    if (!containerRef.current) return
    const initial = parseCoord(latitude, longitude)
    const map = L.map(containerRef.current, {
      center: initial ?? defaultCenter ?? DEFAULT_CENTER,
      zoom: initial ? 14 : defaultCenter ? 13 : 2,
      worldCopyJump: true,
    })
    mapRef.current = map

    const satellite = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, attribution: 'Imagery &copy; Esri' },
    )
    const labels = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19 },
    )
    const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    })
    const hybrid = L.layerGroup([satellite, labels]).addTo(map)
    L.control.layers({ Satellite: hybrid, Map: streets }, undefined, { position: 'topright' }).addTo(map)

    if (initial) placeMarker(initial)
    map.on('click', (e: L.LeafletMouseEvent) => pickRef.current(e.latlng.lat, e.latlng.lng))

    // The map mounts inside an animating dialog; recompute size once it settles.
    const ro = new ResizeObserver(() => map.invalidateSize())
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Keep the marker in sync when the user types coordinates by hand.
  useEffect(() => {
    const map = mapRef.current
    const ll = parseCoord(latitude, longitude)
    if (!map || !ll) return
    const current = markerRef.current?.getLatLng()
    if (current && round6(current.lat) === round6(ll[0]) && round6(current.lng) === round6(ll[1])) return
    placeMarker(ll)
    map.setView(ll, Math.max(map.getZoom(), 12))
  }, [latitude, longitude])

  // Re-centre on a new default (e.g. a different farm selected) until a point is picked.
  const centerKey = defaultCenter ? `${defaultCenter[0]},${defaultCenter[1]}` : ''
  useEffect(() => {
    if (!mapRef.current || markerRef.current || !defaultCenter) return
    mapRef.current.setView(defaultCenter, 13)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [centerKey])

  async function handleSearch() {
    const q = query.trim()
    if (!q) return
    setSearching(true)
    setMessage(null)
    try {
      const res = await fetch(`${NOMINATIM}/search?format=jsonv2&limit=1&q=${encodeURIComponent(q)}`)
      const results = res.ok ? await res.json() : []
      if (!results.length) {
        setMessage('No place found for that search.')
        return
      }
      pickRef.current(Number(results[0].lat), Number(results[0].lon), 14)
    } catch {
      setMessage('Search failed. Check your connection.')
    } finally {
      setSearching(false)
    }
  }

  function handleLocate() {
    if (!navigator.geolocation) {
      setMessage('Geolocation is not supported by this browser.')
      return
    }
    setLocating(true)
    setMessage(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        pickRef.current(pos.coords.latitude, pos.coords.longitude, 15)
      },
      () => {
        setLocating(false)
        setMessage('Could not get your location.')
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          placeholder="Search a place, village or address…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault() // don't submit the farm form
              handleSearch()
            }
          }}
        />
        <Button type="button" variant="outline" size="icon" onClick={handleSearch} disabled={searching} title="Search">
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        </Button>
        <Button type="button" variant="outline" size="icon" onClick={handleLocate} disabled={locating} title="Use my location">
          {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Crosshair className="h-4 w-4" />}
        </Button>
      </div>
      <div ref={containerRef} className="h-64 w-full overflow-hidden rounded-md border border-input z-0" />
      <p className="text-xs text-muted-foreground">
        {message ?? 'Click the map or drag the pin to set the farm location.'}
      </p>
    </div>
  )
}
