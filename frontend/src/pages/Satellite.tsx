import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts'
import type { TooltipProps } from 'recharts'
import { Satellite as SatelliteIcon, Cloud, TrendingUp, TrendingDown, Minus, ImageIcon, Plus, Pencil, Trash2, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import {
  useSatelliteAnalyses, useCreateSatelliteAnalysis,
  useUpdateSatelliteAnalysis, useDeleteSatelliteAnalysis,
} from '@/api/satellite'
import { formatDate } from '@/lib/utils'
import type { SatelliteAnalysis, SatelliteSource } from '@/types'

// ─── Satellite meta ───────────────────────────────────────────────────────────

const SOURCE_LABEL: Record<SatelliteSource, string> = {
  sentinel_2: 'Sentinel-2',
  landsat_8: 'Landsat 8',
  landsat_9: 'Landsat 9',
  planet: 'Planet',
  modis: 'MODIS',
  spot: 'SPOT',
}

// Vegetation indices config
const INDICES = [
  { key: 'ndvi', label: 'NDVI', color: '#22c55e', range: [-1, 1] },
  { key: 'ndwi', label: 'NDWI', color: '#3b82f6', range: [-1, 1] },
  { key: 'ndre', label: 'NDRE', color: '#f97316', range: [-1, 1] },
  { key: 'evi',  label: 'EVI',  color: '#8b5cf6', range: [-1, 2] },
] as const

type IndexKey = 'ndvi' | 'ndwi' | 'ndre' | 'evi'

// ─── NDVI health classification ───────────────────────────────────────────────

function ndviClass(v: number): { label: string; color: string; textClass: string } {
  if (v < 0)    return { label: 'Water / No Data', color: '#0ea5e9', textClass: 'text-sky-600' }
  if (v < 0.1)  return { label: 'Bare Soil',        color: '#ef4444', textClass: 'text-red-600' }
  if (v < 0.25) return { label: 'Sparse',           color: '#f97316', textClass: 'text-orange-600' }
  if (v < 0.4)  return { label: 'Moderate',         color: '#f59e0b', textClass: 'text-amber-600' }
  if (v < 0.6)  return { label: 'Good',             color: '#84cc16', textClass: 'text-lime-600' }
  if (v < 0.75) return { label: 'Dense',            color: '#22c55e', textClass: 'text-green-600' }
  return         { label: 'Excellent',              color: '#15803d', textClass: 'text-green-800' }
}

// Horizontal NDVI gradient bar with pin (0..1 range for agri use)
function NdviBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(1, value))
  const pct = clamped * 100
  const { label, color } = ndviClass(value)
  return (
    <div className="space-y-1">
      <div className="relative h-4 w-full rounded-full overflow-hidden"
        style={{ background: 'linear-gradient(to right, #ef4444, #f97316, #f59e0b, #84cc16, #22c55e, #15803d)' }}
      >
        {/* pin */}
        <div
          className="absolute top-0 h-full w-0.5 -translate-x-1/2 bg-white shadow"
          style={{ left: `${pct}%` }}
        />
        {/* value bubble */}
        <div
          className="absolute -top-6 -translate-x-1/2 rounded px-1 py-0.5 text-xs font-bold text-white"
          style={{ left: `${pct}%`, background: color }}
        >
          {value.toFixed(3)}
        </div>
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>0.0</span>
        <span className="font-medium" style={{ color }}>{label}</span>
        <span>1.0</span>
      </div>
    </div>
  )
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      {payload.map(p => p.value != null ? (
        <p key={p.dataKey} className="font-medium" style={{ color: p.color }}>
          {p.name}: {Number(p.value).toFixed(4)}
        </p>
      ) : null)}
    </div>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const inRange = (min: number, max: number) => (v: string) =>
  v === '' || (!isNaN(Number(v)) && Number(v) >= min && Number(v) <= max)

const analysisSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  acquisition_date: z.string().min(1, 'Acquisition date is required'),
  satellite_source: z.string(),
  cloud_cover_percentage: z.string().refine(inRange(0, 100), { message: 'Enter 0–100' }),
  ndvi: z.string().refine(inRange(-1, 1), { message: 'Enter −1 to 1' }),
  ndwi: z.string().refine(inRange(-1, 1), { message: 'Enter −1 to 1' }),
  ndre: z.string().refine(inRange(-1, 1), { message: 'Enter −1 to 1' }),
  evi:  z.string().refine(inRange(-1, 2), { message: 'Enter −1 to 2' }),
  image_url: z.string(),
  notes: z.string(),
})

interface AnalysisFormValues {
  farm_id: string; field_id: string; acquisition_date: string
  satellite_source: string; cloud_cover_percentage: string
  ndvi: string; ndwi: string; ndre: string; evi: string
  image_url: string; notes: string
}

const defaultValues: AnalysisFormValues = {
  farm_id: '', field_id: '',
  acquisition_date: new Date().toISOString().slice(0, 10),
  satellite_source: '', cloud_cover_percentage: '',
  ndvi: '', ndwi: '', ndre: '', evi: '',
  image_url: '', notes: '',
}

function analysisToFormValues(
  a: SatelliteAnalysis,
  allFields: { id: number; farm_id: number }[],
): AnalysisFormValues {
  const field = allFields.find(f => f.id === a.field_id)
  return {
    farm_id: field ? String(field.farm_id) : '',
    field_id: String(a.field_id),
    acquisition_date: a.acquisition_date.slice(0, 10),
    satellite_source: a.satellite_source ?? '',
    cloud_cover_percentage: a.cloud_cover_percentage != null ? String(a.cloud_cover_percentage) : '',
    ndvi: a.ndvi != null ? String(a.ndvi) : '',
    ndwi: a.ndwi != null ? String(a.ndwi) : '',
    ndre: a.ndre != null ? String(a.ndre) : '',
    evi:  a.evi  != null ? String(a.evi)  : '',
    image_url: a.image_url ?? '',
    notes: a.notes ?? '',
  }
}

// ─── Create / Edit dialog ─────────────────────────────────────────────────────

interface AnalysisDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: SatelliteAnalysis | null
  allFields: { id: number; name: string; farm_id: number }[]
}

function AnalysisDialog({ open, onOpenChange, editing, allFields }: AnalysisDialogProps) {
  const { data: farms = [] } = useFarms()
  const createAnalysis = useCreateSatelliteAnalysis()
  const updateAnalysis = useUpdateSatelliteAnalysis()

  const form = useForm<AnalysisFormValues>({
    resolver: zodResolver(analysisSchema),
    defaultValues,
  })
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors } } = form

  const watchedFarm = watch('farm_id')
  const { data: fields = [] } = useFields(watchedFarm ? Number(watchedFarm) : undefined)

  useEffect(() => {
    if (editing) reset(analysisToFormValues(editing, allFields))
    else reset(defaultValues)
  }, [editing, allFields, reset])

  useEffect(() => { if (!editing) setValue('field_id', '') }, [watchedFarm, editing, setValue])

  const opt = (v: string) => v ? Number(v) : undefined

  const onSubmit = (values: AnalysisFormValues) => {
    const payload = {
      acquisition_date: values.acquisition_date,
      satellite_source: (values.satellite_source as SatelliteSource) || undefined,
      cloud_cover_percentage: opt(values.cloud_cover_percentage),
      ndvi: opt(values.ndvi),
      ndwi: opt(values.ndwi),
      ndre: opt(values.ndre),
      evi:  opt(values.evi),
      image_url: values.image_url || undefined,
      notes: values.notes || undefined,
    }

    if (editing) {
      updateAnalysis.mutate(
        { id: editing.id, payload },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    } else {
      createAnalysis.mutate(
        { ...payload, field_id: Number(values.field_id) },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    }
  }

  const isPending = createAnalysis.isPending || updateAnalysis.isPending

  return (
    <Dialog open={open} onOpenChange={v => { onOpenChange(v); if (!v) reset(defaultValues) }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit Satellite Analysis' : 'Add Satellite Analysis'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">

            {/* Farm — locked in edit */}
            <div className="space-y-1.5">
              <Label>Farm</Label>
              {editing ? (
                <Input
                  value={farms.find(f => f.id === allFields.find(fi => fi.id === editing.field_id)?.farm_id)?.name ?? '—'}
                  readOnly className="bg-muted text-muted-foreground"
                />
              ) : (
                <Controller name="farm_id" control={control} render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue placeholder="Select farm" /></SelectTrigger>
                    <SelectContent>
                      {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                )} />
              )}
              {errors.farm_id && <p className="text-xs text-destructive">{errors.farm_id.message}</p>}
            </div>

            {/* Field — locked in edit */}
            <div className="space-y-1.5">
              <Label>Field</Label>
              {editing ? (
                <Input
                  value={allFields.find(f => f.id === editing.field_id)?.name ?? '—'}
                  readOnly className="bg-muted text-muted-foreground"
                />
              ) : (
                <Controller name="field_id" control={control} render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange} disabled={!watchedFarm}>
                    <SelectTrigger>
                      <SelectValue placeholder={watchedFarm ? 'Select field' : 'Select farm first'} />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                )} />
              )}
              {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
            </div>

            {/* Acquisition date */}
            <div className="space-y-1.5">
              <Label>Acquisition Date</Label>
              <Input type="date" {...register('acquisition_date')} />
              {errors.acquisition_date && <p className="text-xs text-destructive">{errors.acquisition_date.message}</p>}
            </div>

            {/* Satellite source */}
            <div className="space-y-1.5">
              <Label>Satellite Source <span className="text-muted-foreground">(optional)</span></Label>
              <Controller name="satellite_source" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="— Unknown —" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— Unknown —</SelectItem>
                    {(Object.keys(SOURCE_LABEL) as SatelliteSource[]).map(s => (
                      <SelectItem key={s} value={s}>{SOURCE_LABEL[s]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Cloud cover */}
            <div className="space-y-1.5">
              <Label>Cloud Cover % <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="number" min="0" max="100" step="0.1" placeholder="e.g. 5" {...register('cloud_cover_percentage')} />
              {errors.cloud_cover_percentage && <p className="text-xs text-destructive">{errors.cloud_cover_percentage.message}</p>}
            </div>

            {/* Spacer */}
            <div />
          </div>

          {/* Vegetation indices */}
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Vegetation Indices</p>
          <div className="grid grid-cols-2 gap-3">
            {INDICES.map(idx => (
              <div key={idx.key} className="space-y-1.5">
                <Label>
                  <span style={{ color: idx.color }} className="font-semibold">{idx.label}</span>
                  {' '}
                  <span className="text-muted-foreground font-normal">({idx.range[0]}…{idx.range[1]})</span>
                </Label>
                <Input
                  type="number"
                  step="0.0001"
                  min={idx.range[0]}
                  max={idx.range[1]}
                  placeholder={`e.g. 0.65`}
                  {...register(idx.key)}
                />
                {errors[idx.key] && <p className="text-xs text-destructive">{errors[idx.key]?.message}</p>}
              </div>
            ))}
          </div>

          {/* Image URL */}
          <div className="space-y-1.5">
            <Label>Image URL <span className="text-muted-foreground">(optional)</span></Label>
            <Input type="url" placeholder="https://…" {...register('image_url')} />
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label>Notes <span className="text-muted-foreground">(optional)</span></Label>
            <Textarea placeholder="Acquisition notes, processing flags…" rows={2} {...register('notes')} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { onOpenChange(false); reset(defaultValues) }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? (editing ? 'Saving…' : 'Adding…') : editing ? 'Save Changes' : 'Add Analysis'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete dialog ────────────────────────────────────────────────────────────

interface DeleteDialogProps {
  analysis: SatelliteAnalysis | null
  onOpenChange: (v: boolean) => void
}

function DeleteDialog({ analysis, onOpenChange }: DeleteDialogProps) {
  const deleteAnalysis = useDeleteSatelliteAnalysis()
  if (!analysis) return null
  return (
    <Dialog open={!!analysis} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Satellite Analysis</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-800">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>Stored in a <strong>TimescaleDB hypertable</strong> — cannot be recovered after deletion.</span>
              </div>
              <p>
                Delete acquisition from <strong>{formatDate(analysis.acquisition_date)}</strong>
                {analysis.satellite_source ? ` (${SOURCE_LABEL[analysis.satellite_source]})` : ''}?
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={deleteAnalysis.isPending}
            onClick={() => deleteAnalysis.mutate(analysis.id, { onSuccess: () => onOpenChange(false) })}
          >
            {deleteAnalysis.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Latest health panel ──────────────────────────────────────────────────────

function LatestHealthPanel({ latest }: { latest: SatelliteAnalysis | null }) {
  if (!latest) {
    return (
      <div className="flex h-full min-h-40 items-center justify-center text-muted-foreground text-sm">
        No acquisitions in range
      </div>
    )
  }

  const { label, textClass } = latest.ndvi != null ? ndviClass(latest.ndvi) : { label: '—', textClass: 'text-muted-foreground' }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">Acquisition</p>
          <p className="font-semibold">{formatDate(latest.acquisition_date)}</p>
        </div>
        {latest.satellite_source && (
          <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
            {SOURCE_LABEL[latest.satellite_source]}
          </span>
        )}
      </div>

      {latest.ndvi != null ? (
        <div className="space-y-3 pt-2">
          <p className={`text-sm font-semibold ${textClass}`}>Vegetation Health: {label}</p>
          <NdviBar value={latest.ndvi} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No NDVI data for this acquisition</p>
      )}

      {/* Index values */}
      <div className="grid grid-cols-2 gap-2 pt-1">
        {INDICES.map(idx => {
          const val = latest[idx.key as keyof SatelliteAnalysis] as number | null
          return (
            <div key={idx.key} className="rounded-lg bg-muted/50 px-3 py-2">
              <p className="text-xs font-medium" style={{ color: idx.color }}>{idx.label}</p>
              <p className="mt-0.5 font-mono text-sm font-bold">
                {val != null ? val.toFixed(4) : <span className="text-muted-foreground font-normal text-xs">—</span>}
              </p>
            </div>
          )
        })}
        {latest.cloud_cover_percentage != null && (
          <div className="col-span-2 rounded-lg bg-muted/50 px-3 py-2">
            <p className="text-xs font-medium text-sky-500">Cloud Cover</p>
            <p className="mt-0.5 font-mono text-sm font-bold">{latest.cloud_cover_percentage.toFixed(1)}%</p>
          </div>
        )}
      </div>

      {latest.image_url && (
        <a
          href={latest.image_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline"
        >
          <ImageIcon className="size-3.5" /> View source image
        </a>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Satellite() {
  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [visibleIndices, setVisibleIndices] = useState<Record<IndexKey, boolean>>({
    ndvi: true, ndwi: true, ndre: false, evi: false,
  })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<SatelliteAnalysis | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<SatelliteAnalysis | null>(null)

  const now = new Date()
  const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
  const [fromDate, setFromDate] = useState(oneYearAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10))

  const { data: farms = [] } = useFarms()
  const { data: fields = [] } = useFields(selectedFarmId)
  const { data: allFieldsFlat = [] } = useFields()

  const { data: analyses = [], isLoading } = useSatelliteAnalyses({
    fieldId: selectedFieldId,
    from: fromDate ? `${fromDate}T00:00:00Z` : undefined,
    to: toDate ? `${toDate}T23:59:59Z` : undefined,
  })

  const sorted = useMemo(
    () => [...analyses].sort((a, b) => a.acquisition_date.localeCompare(b.acquisition_date)),
    [analyses],
  )

  const latest = sorted[sorted.length - 1] ?? null
  const prev = sorted[sorted.length - 2] ?? null

  // Stats
  const stats = useMemo(() => {
    const ndviValues = sorted.filter(a => a.ndvi != null).map(a => a.ndvi!)
    const avgNdvi = ndviValues.length
      ? ndviValues.reduce((s, v) => s + v, 0) / ndviValues.length : null
    const avgCloud = analyses.filter(a => a.cloud_cover_percentage != null).length > 0
      ? analyses.reduce((s, a) => s + (a.cloud_cover_percentage ?? 0), 0) /
        analyses.filter(a => a.cloud_cover_percentage != null).length
      : null
    const ndviTrend = latest?.ndvi != null && prev?.ndvi != null
      ? latest.ndvi - prev.ndvi : null
    return { count: analyses.length, avgNdvi, avgCloud, ndviTrend }
  }, [analyses, sorted, latest, prev])

  // Chart data
  const chartData = useMemo(() =>
    sorted.map(a => ({
      date: new Date(a.acquisition_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      ndvi: a.ndvi,
      ndwi: a.ndwi,
      ndre: a.ndre,
      evi:  a.evi,
    })),
    [sorted],
  )

  function toggleIndex(key: IndexKey) {
    setVisibleIndices(prev => ({ ...prev, [key]: !prev[key] }))
  }

  function openCreate() { setEditing(null); setDialogOpen(true) }
  function openEdit(a: SatelliteAnalysis) { setEditing(a); setDialogOpen(true) }

  const TrendIcon = stats.ndviTrend == null
    ? Minus
    : stats.ndviTrend > 0.01 ? TrendingUp : stats.ndviTrend < -0.01 ? TrendingDown : Minus

  const trendColor = stats.ndviTrend == null ? 'text-muted-foreground'
    : stats.ndviTrend > 0.01 ? 'text-green-600' : stats.ndviTrend < -0.01 ? 'text-red-600' : 'text-muted-foreground'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Satellite Analysis</h1>
          <p className="text-sm text-muted-foreground">
            Vegetation indices from satellite imagery · NDVI, NDWI, NDRE, EVI
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 size-4" /> Add Analysis
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select
          value={selectedFarmId ? String(selectedFarmId) : 'all'}
          onValueChange={v => {
            setSelectedFarmId(v !== 'all' ? Number(v) : undefined)
            setSelectedFieldId(undefined)
          }}
        >
          <SelectTrigger className="w-44"><SelectValue placeholder="All farms" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All farms</SelectItem>
            {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select
          value={selectedFieldId ? String(selectedFieldId) : 'all'}
          onValueChange={v => setSelectedFieldId(v !== 'all' ? Number(v) : undefined)}
          disabled={!selectedFarmId}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder={selectedFarmId ? 'All fields' : 'Select farm'} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All fields</SelectItem>
            {fields.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-2">
          <Input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} className="w-36" />
          <span className="text-muted-foreground text-sm">to</span>
          <Input type="date" value={toDate} onChange={e => setToDate(e.target.value)} className="w-36" />
        </div>
      </div>

      {/* Stat cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-lg" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <SatelliteIcon className="size-4" /> Acquisitions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.count}</p>
              <p className="mt-1 text-xs text-muted-foreground">In selected range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <span className="size-4 font-bold text-green-600 text-sm">N</span> Latest NDVI
              </CardTitle>
            </CardHeader>
            <CardContent>
              {latest?.ndvi != null ? (
                <>
                  <p className={`text-3xl font-bold ${ndviClass(latest.ndvi).textClass}`}>
                    {latest.ndvi.toFixed(3)}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{ndviClass(latest.ndvi).label}</p>
                </>
              ) : (
                <p className="text-3xl font-bold">—</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <TrendIcon className={`size-4 ${trendColor}`} /> NDVI Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-3xl font-bold ${trendColor}`}>
                {stats.ndviTrend != null
                  ? `${stats.ndviTrend > 0 ? '+' : ''}${stats.ndviTrend.toFixed(3)}`
                  : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">vs previous acquisition</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Cloud className="size-4" /> Avg Cloud Cover
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.avgCloud != null ? `${stats.avgCloud.toFixed(1)}%` : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Period average</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart + Latest health panel */}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Vegetation Indices Over Time</CardTitle>
              {/* Index toggles */}
              <div className="flex gap-1.5">
                {INDICES.map(idx => (
                  <button
                    key={idx.key}
                    onClick={() => toggleIndex(idx.key)}
                    className={`rounded-full px-2 py-0.5 text-xs font-medium transition-opacity ${
                      visibleIndices[idx.key] ? 'opacity-100' : 'opacity-30'
                    }`}
                    style={{
                      background: `${idx.color}22`,
                      color: idx.color,
                      border: `1px solid ${idx.color}`,
                    }}
                  >
                    {idx.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
                No satellite acquisitions in the selected range
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                  <YAxis domain={[-0.2, 1]} tick={{ fontSize: 11 }} width={36} />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Legend />
                  <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
                  {INDICES.map(idx =>
                    visibleIndices[idx.key] ? (
                      <Line
                        key={idx.key}
                        type="monotone"
                        dataKey={idx.key}
                        name={idx.label}
                        stroke={idx.color}
                        strokeWidth={2}
                        dot={chartData.length < 20}
                        activeDot={{ r: 4 }}
                        connectNulls
                      />
                    ) : null,
                  )}
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Latest Acquisition</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : (
              <LatestHealthPanel latest={latest} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Acquisitions table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Acquisition Log
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({analyses.length} {analyses.length === 1 ? 'record' : 'records'})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : analyses.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground text-sm">
              No satellite analyses found — add the first acquisition above
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Date</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Source</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Cloud %</th>
                    {INDICES.map(idx => (
                      <th key={idx.key} className="px-4 py-2 text-right text-xs font-semibold" style={{ color: idx.color }}>
                        {idx.label}
                      </th>
                    ))}
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {[...analyses]
                    .sort((a, b) => b.acquisition_date.localeCompare(a.acquisition_date))
                    .map(a => (
                      <tr key={a.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-4 py-2 font-mono text-xs">{formatDate(a.acquisition_date)}</td>
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {a.satellite_source ? SOURCE_LABEL[a.satellite_source] : '—'}
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-xs">
                          {a.cloud_cover_percentage != null ? `${a.cloud_cover_percentage.toFixed(1)}%` : '—'}
                        </td>
                        {INDICES.map(idx => {
                          const val = a[idx.key as keyof SatelliteAnalysis] as number | null
                          return (
                            <td key={idx.key} className="px-4 py-2 text-right font-mono text-xs">
                              {val != null ? (
                                <span style={{ color: idx.key === 'ndvi' ? ndviClass(val).color : undefined }}>
                                  {val.toFixed(4)}
                                </span>
                              ) : '—'}
                            </td>
                          )
                        })}
                        <td className="px-4 py-2">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-foreground"
                              onClick={() => openEdit(a)}
                            >
                              <Pencil className="size-3.5" />
                            </Button>
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-destructive"
                              onClick={() => setDeleteTarget(a)}
                            >
                              <Trash2 className="size-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <AnalysisDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        allFields={allFieldsFlat}
      />
      <DeleteDialog analysis={deleteTarget} onOpenChange={v => { if (!v) setDeleteTarget(null) }} />
    </div>
  )
}
