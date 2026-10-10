import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Droplets, Clock, Activity, CalendarDays, Plus, Pencil, Trash2, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { useCrops } from '@/api/crops'
import {
  useIrrigationEvents, useCreateIrrigationEvent,
  useUpdateIrrigationEvent, useDeleteIrrigationEvent,
} from '@/api/irrigation'
import { formatDateTime } from '@/lib/utils'
import type { IrrigationEvent, IrrigationMethod } from '@/types'

// ─── Irrigation meta ──────────────────────────────────────────────────────────

const ALL_METHODS: IrrigationMethod[] = [
  'drip', 'sprinkler', 'flood', 'furrow', 'center_pivot', 'subsurface',
]

const METHOD_LABEL: Record<IrrigationMethod, string> = {
  drip: 'Drip',
  sprinkler: 'Sprinkler',
  flood: 'Flood',
  furrow: 'Furrow',
  center_pivot: 'Center Pivot',
  subsurface: 'Subsurface',
}

const METHOD_COLOR: Record<IrrigationMethod, string> = {
  drip: 'text-blue-700 bg-blue-100',
  sprinkler: 'text-sky-700 bg-sky-100',
  flood: 'text-indigo-700 bg-indigo-100',
  furrow: 'text-amber-700 bg-amber-100',
  center_pivot: 'text-green-700 bg-green-100',
  subsurface: 'text-violet-700 bg-violet-100',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toDatetimeLocal(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function nowDatetimeLocal() {
  return toDatetimeLocal(new Date().toISOString())
}

function formatDuration(minutes: number | null) {
  if (minutes === null) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ dataKey?: string; name?: string; value?: number; color?: string }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} className="font-medium" style={{ color: p.color }}>
          {p.name}: {Number(p.value).toFixed(1)}{' '}
          {p.dataKey === 'water' ? 'L' : p.dataKey === 'events' ? 'events' : 'min'}
        </p>
      ))}
    </div>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const eventSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  crop_id: z.string(),
  irrigation_method: z.string().min(1, 'Select an irrigation method'),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string(),
  duration_minutes: z.string().refine(v => v === '' || !isNaN(Number(v)), { message: 'Must be a number' }),
  water_amount: z.string().refine(v => v === '' || !isNaN(Number(v)), { message: 'Must be a number' }),
  notes: z.string(),
})

interface EventFormValues {
  farm_id: string
  field_id: string
  crop_id: string
  irrigation_method: string
  start_time: string
  end_time: string
  duration_minutes: string
  water_amount: string
  notes: string
}

const defaultValues: EventFormValues = {
  farm_id: '', field_id: '', crop_id: '',
  irrigation_method: '', start_time: nowDatetimeLocal(),
  end_time: '', duration_minutes: '', water_amount: '', notes: '',
}

function eventToFormValues(e: IrrigationEvent, fields: import('@/types').Field[]): EventFormValues {
  const match = fields.find((f) => f.id === e.field_id)
  return {
    farm_id: match ? String(match.farm_id) : '',
    field_id: String(e.field_id),
    crop_id: e.crop_id ? String(e.crop_id) : '',
    irrigation_method: e.irrigation_method,
    start_time: toDatetimeLocal(e.start_time),
    end_time: e.end_time ? toDatetimeLocal(e.end_time) : '',
    duration_minutes: e.duration_minutes != null ? String(e.duration_minutes) : '',
    water_amount: e.water_amount != null ? String(e.water_amount) : '',
    notes: e.notes ?? '',
  }
}

// ─── Create / Edit dialog ─────────────────────────────────────────────────────

interface EventDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: IrrigationEvent | null
  allFields: import('@/types').Field[]
}

function EventDialog({ open, onOpenChange, editing, allFields }: EventDialogProps) {
  const { data: farms = [] } = useFarms()
  const createEvent = useCreateIrrigationEvent()
  const updateEvent = useUpdateIrrigationEvent()

  const form = useForm<EventFormValues>({
    resolver: zodResolver(eventSchema),
    defaultValues,
  })
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors } } = form

  const watchedFarm = watch('farm_id')
  const watchedField = watch('field_id')

  const { data: fields = [] } = useFields(watchedFarm || undefined)
  const { data: crops = [] } = useCrops(watchedField || undefined)

  // Populate form when editing
  useEffect(() => {
    if (editing) {
      reset(eventToFormValues(editing, allFields))
    } else {
      reset(defaultValues)
    }
  }, [editing, allFields, reset])

  // Reset field when farm changes (only in create mode)
  useEffect(() => {
    if (!editing) setValue('field_id', '')
  }, [watchedFarm, editing, setValue])

  useEffect(() => {
    if (!editing) setValue('crop_id', '')
  }, [watchedField, editing, setValue])

  const onSubmit = (values: EventFormValues) => {
    const payload = {
      crop_id: values.crop_id ? Number(values.crop_id) : undefined,
      irrigation_method: values.irrigation_method as IrrigationMethod,
      start_time: new Date(values.start_time).toISOString(),
      end_time: values.end_time ? new Date(values.end_time).toISOString() : undefined,
      duration_minutes: values.duration_minutes ? Number(values.duration_minutes) : undefined,
      water_amount: values.water_amount ? Number(values.water_amount) : undefined,
      notes: values.notes || undefined,
    }

    if (editing) {
      updateEvent.mutate(
        { id: editing.id, payload },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    } else {
      createEvent.mutate(
        { ...payload, field_id: values.field_id },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    }
  }

  const isPending = createEvent.isPending || updateEvent.isPending

  return (
    <Dialog open={open} onOpenChange={v => { onOpenChange(v); if (!v) reset(defaultValues) }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit Irrigation Event' : 'Log Irrigation Event'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {/* Farm — locked in edit mode */}
            <div className="space-y-1.5">
              <Label>Farm</Label>
              {editing ? (
                <Input
                  value={farms.find(f => f.id === allFields.find(fi => fi.id === editing.field_id)?.farm_id)?.farm_name ?? '—'}
                  readOnly
                  className="bg-muted text-muted-foreground"
                />
              ) : (
                <Controller name="farm_id" control={control} render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue placeholder="Select farm" /></SelectTrigger>
                    <SelectContent>
                      {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.farm_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                )} />
              )}
              {errors.farm_id && <p className="text-xs text-destructive">{errors.farm_id.message}</p>}
            </div>

            {/* Field — locked in edit mode */}
            <div className="space-y-1.5">
              <Label>Field</Label>
              {editing ? (
                <Input
                  value={allFields.find(f => f.id === editing.field_id)?.name ?? '—'}
                  readOnly
                  className="bg-muted text-muted-foreground"
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

            {/* Crop (optional) */}
            <div className="space-y-1.5">
              <Label>Crop <span className="text-muted-foreground">(optional)</span></Label>
              <Controller name="crop_id" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={!watchedField && !editing}>
                  <SelectTrigger>
                    <SelectValue placeholder="— No crop —" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— No crop —</SelectItem>
                    {crops.map(c => (
                      <SelectItem key={c.id} value={String(c.id)}>{c.name}{c.variety ? ` (${c.variety})` : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Method */}
            <div className="space-y-1.5">
              <Label>Irrigation Method</Label>
              <Controller name="irrigation_method" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
                  <SelectContent>
                    {ALL_METHODS.map(m => (
                      <SelectItem key={m} value={m}>{METHOD_LABEL[m]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
              {errors.irrigation_method && <p className="text-xs text-destructive">{errors.irrigation_method.message}</p>}
            </div>

            {/* Start time */}
            <div className="space-y-1.5">
              <Label>Start Time</Label>
              <Input type="datetime-local" {...register('start_time')} readOnly={!!editing} className={editing ? 'bg-muted text-muted-foreground' : ''} />
              {errors.start_time && <p className="text-xs text-destructive">{errors.start_time.message}</p>}
            </div>

            {/* End time */}
            <div className="space-y-1.5">
              <Label>End Time <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="datetime-local" {...register('end_time')} />
            </div>

            {/* Duration */}
            <div className="space-y-1.5">
              <Label>Duration (minutes)</Label>
              <Input type="number" min="0" placeholder="e.g. 90" {...register('duration_minutes')} />
              {errors.duration_minutes && <p className="text-xs text-destructive">{errors.duration_minutes.message}</p>}
            </div>

            {/* Water amount */}
            <div className="space-y-1.5">
              <Label>Water Amount (L)</Label>
              <Input type="number" min="0" step="0.1" placeholder="e.g. 500" {...register('water_amount')} />
              {errors.water_amount && <p className="text-xs text-destructive">{errors.water_amount.message}</p>}
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label>Notes <span className="text-muted-foreground">(optional)</span></Label>
            <Textarea placeholder="Any observations or remarks…" rows={2} {...register('notes')} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { onOpenChange(false); reset(defaultValues) }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? (editing ? 'Saving…' : 'Logging…') : editing ? 'Save Changes' : 'Log Event'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete dialog ────────────────────────────────────────────────────────────

interface DeleteDialogProps {
  event: IrrigationEvent | null
  onOpenChange: (v: boolean) => void
}

function DeleteDialog({ event, onOpenChange }: DeleteDialogProps) {
  const deleteEvent = useDeleteIrrigationEvent()
  if (!event) return null
  return (
    <Dialog open={!!event} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Irrigation Event</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-800">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>This action cannot be undone.</span>
              </div>
              <p>
                Delete <strong>{METHOD_LABEL[event.irrigation_method]}</strong> irrigation event
                started at {formatDateTime(event.start_time)}?
                {event.water_amount != null && (
                  <span> ({event.water_amount.toLocaleString()} L applied)</span>
                )}
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={deleteEvent.isPending}
            onClick={() =>
              deleteEvent.mutate(event.id, { onSuccess: () => onOpenChange(false) })
            }
          >
            {deleteEvent.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Irrigation() {
  const [selectedFarmId, setSelectedFarmId] = useState<string | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<IrrigationEvent | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<IrrigationEvent | null>(null)

  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  const [fromDate, setFromDate] = useState(thirtyDaysAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10))

  const { data: farms = [] } = useFarms()
  const { data: fields = [] } = useFields(selectedFarmId)

  // All fields flattened for form lookups (farm_id resolution)
  const { data: allFieldsFlat = [] } = useFields()

  const { data: events = [], isLoading } = useIrrigationEvents({
    fieldId: selectedFieldId,
    from: fromDate ? `${fromDate}T00:00:00Z` : undefined,
    to: toDate ? `${toDate}T23:59:59Z` : undefined,
  })

  // Stats
  const stats = useMemo(() => {
    const totalWater = events.reduce((s, e) => s + (e.water_amount ?? 0), 0)
    const durations = events.filter(e => e.duration_minutes != null).map(e => e.duration_minutes!)
    const avgDuration = durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : null
    const sorted = [...events].sort((a, b) => a.start_time.localeCompare(b.start_time))
    const latest = sorted[sorted.length - 1]?.start_time ?? null
    return { count: events.length, totalWater, avgDuration, latest }
  }, [events])

  // Daily aggregation for chart
  const chartData = useMemo(() => {
    const byDay: Record<string, { water: number; events: number; duration: number }> = {}
    events.forEach(e => {
      const day = e.start_time.slice(0, 10)
      if (!byDay[day]) byDay[day] = { water: 0, events: 0, duration: 0 }
      byDay[day].water += e.water_amount ?? 0
      byDay[day].events += 1
      byDay[day].duration += e.duration_minutes ?? 0
    })
    return Object.entries(byDay)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, v]) => ({
        date: new Date(date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        water: v.water,
        events: v.events,
        duration: v.duration,
      }))
  }, [events])

  function openCreate() { setEditing(null); setDialogOpen(true) }
  function openEdit(e: IrrigationEvent) { setEditing(e); setDialogOpen(true) }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Irrigation Events</h1>
          <p className="text-sm text-muted-foreground">
            Field irrigation log · Water usage tracking and history
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 size-4" /> Log Event
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select
          value={selectedFarmId ? String(selectedFarmId) : 'all'}
          onValueChange={v => {
            setSelectedFarmId(v !== 'all' ? v : undefined)
            setSelectedFieldId(undefined)
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All farms" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All farms</SelectItem>
            {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.farm_name}</SelectItem>)}
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
          <Input
            type="date"
            value={fromDate}
            onChange={e => setFromDate(e.target.value)}
            className="w-36"
          />
          <span className="text-muted-foreground text-sm">to</span>
          <Input
            type="date"
            value={toDate}
            onChange={e => setToDate(e.target.value)}
            className="w-36"
          />
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
                <Activity className="size-4" /> Total Events
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
                <Droplets className="size-4" /> Total Water Applied
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.totalWater >= 1000
                  ? `${(stats.totalWater / 1000).toFixed(1)}kL`
                  : `${stats.totalWater.toFixed(0)}L`}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Combined volume</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Clock className="size-4" /> Avg Duration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{formatDuration(stats.avgDuration !== null ? Math.round(stats.avgDuration) : null)}</p>
              <p className="mt-1 text-xs text-muted-foreground">Per irrigation event</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <CalendarDays className="size-4" /> Last Irrigated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold leading-tight">
                {stats.latest ? formatDateTime(stats.latest) : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Most recent event</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Water usage chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Daily Water Usage</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-56 w-full" />
          ) : chartData.length === 0 ? (
            <div className="flex h-56 items-center justify-center text-muted-foreground text-sm">
              No irrigation events in the selected date range
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                <YAxis yAxisId="water" tick={{ fontSize: 11 }} tickFormatter={v => `${v}L`} width={52} />
                <YAxis yAxisId="events" orientation="right" tick={{ fontSize: 11 }} allowDecimals={false} width={32} />
                <RechartsTooltip content={<ChartTooltip />} />
                <Legend />
                <Bar
                  yAxisId="water"
                  dataKey="water"
                  name="Water (L)"
                  fill="#3b82f6"
                  radius={[3, 3, 0, 0]}
                  maxBarSize={40}
                />
                <Line
                  yAxisId="events"
                  type="monotone"
                  dataKey="events"
                  name="Events"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Events table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Event Log
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({events.length} {events.length === 1 ? 'event' : 'events'})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : events.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground text-sm">
              No irrigation events found — log the first one above
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Start Time</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">End Time</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Method</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Duration</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Water (L)</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Notes</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {[...events]
                    .sort((a, b) => b.start_time.localeCompare(a.start_time))
                    .map(e => (
                      <tr key={e.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-4 py-2 font-mono text-xs">
                          {formatDateTime(e.start_time)}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                          {e.end_time ? formatDateTime(e.end_time) : (
                            <Badge variant="secondary" className="text-xs">Ongoing</Badge>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${METHOD_COLOR[e.irrigation_method]}`}>
                            {METHOD_LABEL[e.irrigation_method]}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono">
                          {formatDuration(e.duration_minutes)}
                        </td>
                        <td className="px-4 py-2 text-right font-mono font-semibold">
                          {e.water_amount != null
                            ? e.water_amount.toLocaleString()
                            : <span className="text-muted-foreground font-normal">—</span>}
                        </td>
                        <td className="max-w-48 px-4 py-2 text-xs text-muted-foreground">
                          <span className="line-clamp-1">{e.notes ?? '—'}</span>
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="size-7 text-muted-foreground hover:text-foreground"
                              onClick={() => openEdit(e)}
                            >
                              <Pencil className="size-3.5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="size-7 text-muted-foreground hover:text-destructive"
                              onClick={() => setDeleteTarget(e)}
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

      <EventDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        allFields={allFieldsFlat}
      />
      <DeleteDialog event={deleteTarget} onOpenChange={v => { if (!v) setDeleteTarget(null) }} />
    </div>
  )
}
