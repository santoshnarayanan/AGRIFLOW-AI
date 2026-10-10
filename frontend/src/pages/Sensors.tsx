import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import { Cpu, Activity, Clock, Zap, Plus, Trash2, AlertTriangle, Lock } from 'lucide-react'
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
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import { useSensorReadings, useCreateSensorReading, useDeleteSensorReading } from '@/api/sensors'
import { formatDateTime } from '@/lib/utils'
import type { SensorType, SensorReading } from '@/types'

// ─── Sensor meta ──────────────────────────────────────────────────────────────

const ALL_SENSOR_TYPES: SensorType[] = [
  'soil_moisture', 'soil_temperature', 'air_temperature', 'air_humidity',
  'light_intensity', 'co2_level', 'electrical_conductivity', 'leaf_wetness',
]

const TYPE_LABEL: Record<SensorType, string> = {
  soil_moisture: 'Soil Moisture',
  soil_temperature: 'Soil Temp',
  air_temperature: 'Air Temp',
  air_humidity: 'Air Humidity',
  light_intensity: 'Light Intensity',
  co2_level: 'CO₂ Level',
  electrical_conductivity: 'Elec. Conductivity',
  leaf_wetness: 'Leaf Wetness',
}

const TYPE_UNIT: Record<SensorType, string> = {
  soil_moisture: '%',
  soil_temperature: '°C',
  air_temperature: '°C',
  air_humidity: '%',
  light_intensity: 'lux',
  co2_level: 'ppm',
  electrical_conductivity: 'mS/cm',
  leaf_wetness: '%',
}

const TYPE_COLOR: Record<SensorType, string> = {
  soil_moisture: '#3b82f6',
  soil_temperature: '#f59e0b',
  air_temperature: '#f97316',
  air_humidity: '#0ea5e9',
  light_intensity: '#eab308',
  co2_level: '#22c55e',
  electrical_conductivity: '#8b5cf6',
  leaf_wetness: '#14b8a6',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatChartDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`
}

function toDatetimeLocal(date: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function qualityVariant(flag: string | null): 'success' | 'warning' | 'destructive' | 'secondary' {
  if (!flag) return 'secondary'
  if (flag === 'good') return 'success'
  if (flag === 'questionable') return 'warning'
  return 'destructive'
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
          {p.name}: {Number(p.value).toFixed(2)}
        </p>
      ))}
    </div>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const readingSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  sensor_type: z.string().min(1, 'Select sensor type'),
  sensor_id: z.string(),
  value: z.string().refine(v => v !== '' && !isNaN(Number(v)), { message: 'Enter a valid number' }),
  unit: z.string().min(1, 'Unit is required'),
  quality_flag: z.string(),
  recorded_at: z.string().min(1, 'Recorded at is required'),
})

interface ReadingFormValues {
  farm_id: string
  field_id: string
  sensor_type: string
  sensor_id: string
  value: string
  unit: string
  quality_flag: string
  recorded_at: string
}

// ─── Log Reading dialog ───────────────────────────────────────────────────────

interface LogDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
}

function LogReadingDialog({ open, onOpenChange }: LogDialogProps) {
  const { data: farms = [] } = useFarms()
  const createReading = useCreateSensorReading()

  const form = useForm<ReadingFormValues>({
    resolver: zodResolver(readingSchema),
    defaultValues: {
      farm_id: '', field_id: '', sensor_type: '', sensor_id: '',
      value: '', unit: '', quality_flag: '', recorded_at: toDatetimeLocal(new Date()),
    },
  })
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors } } = form

  const watchedFarm = watch('farm_id')
  const watchedType = watch('sensor_type')
  const { data: fields = [] } = useFields(watchedFarm || undefined)

  useEffect(() => { setValue('field_id', '') }, [watchedFarm, setValue])
  useEffect(() => {
    if (watchedType && TYPE_UNIT[watchedType as SensorType]) {
      setValue('unit', TYPE_UNIT[watchedType as SensorType])
    }
  }, [watchedType, setValue])

  const onSubmit = (values: ReadingFormValues) => {
    createReading.mutate({
      field_id: values.field_id,
      sensor_type: values.sensor_type as SensorType,
      sensor_id: values.sensor_id || undefined,
      value: Number(values.value),
      unit: values.unit,
      quality_flag: values.quality_flag || undefined,
      recorded_at: new Date(values.recorded_at).toISOString(),
    }, {
      onSuccess: () => { onOpenChange(false); reset() },
    })
  }

  return (
    <Dialog open={open} onOpenChange={v => { onOpenChange(v); if (!v) reset() }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Log Sensor Reading</DialogTitle>
          <DialogDescription asChild>
            <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              <Lock className="mt-0.5 size-3.5 shrink-0" />
              <span>Sensor readings are <strong>immutable</strong> once logged. Verify all values before submitting.</span>
            </div>
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {/* Farm */}
            <div className="space-y-1.5">
              <Label>Farm</Label>
              <Controller name="farm_id" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="Select farm" /></SelectTrigger>
                  <SelectContent>
                    {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.farm_name}</SelectItem>)}
                  </SelectContent>
                </Select>
              )} />
              {errors.farm_id && <p className="text-xs text-destructive">{errors.farm_id.message}</p>}
            </div>

            {/* Field */}
            <div className="space-y-1.5">
              <Label>Field</Label>
              <Controller name="field_id" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={!watchedFarm}>
                  <SelectTrigger><SelectValue placeholder={watchedFarm ? 'Select field' : 'Select farm first'} /></SelectTrigger>
                  <SelectContent>
                    {fields.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              )} />
              {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
            </div>

            {/* Sensor Type */}
            <div className="space-y-1.5">
              <Label>Sensor Type</Label>
              <Controller name="sensor_type" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    {ALL_SENSOR_TYPES.map(t => (
                      <SelectItem key={t} value={t}>{TYPE_LABEL[t]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
              {errors.sensor_type && <p className="text-xs text-destructive">{errors.sensor_type.message}</p>}
            </div>

            {/* Sensor ID */}
            <div className="space-y-1.5">
              <Label>Sensor ID <span className="text-muted-foreground">(optional)</span></Label>
              <Input placeholder="e.g. S-001" {...register('sensor_id')} />
            </div>

            {/* Value */}
            <div className="space-y-1.5">
              <Label>Value</Label>
              <Input type="number" step="any" placeholder="0.00" {...register('value')} />
              {errors.value && <p className="text-xs text-destructive">{errors.value.message}</p>}
            </div>

            {/* Unit */}
            <div className="space-y-1.5">
              <Label>Unit</Label>
              <Input placeholder="%" {...register('unit')} />
              {errors.unit && <p className="text-xs text-destructive">{errors.unit.message}</p>}
            </div>

            {/* Quality Flag */}
            <div className="space-y-1.5">
              <Label>Quality Flag <span className="text-muted-foreground">(optional)</span></Label>
              <Controller name="quality_flag" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="— None —" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— None —</SelectItem>
                    <SelectItem value="good">Good</SelectItem>
                    <SelectItem value="questionable">Questionable</SelectItem>
                    <SelectItem value="bad">Bad</SelectItem>
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Recorded At */}
            <div className="space-y-1.5">
              <Label>Recorded At</Label>
              <Input type="datetime-local" {...register('recorded_at')} />
              {errors.recorded_at && <p className="text-xs text-destructive">{errors.recorded_at.message}</p>}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { onOpenChange(false); reset() }}>
              Cancel
            </Button>
            <Button type="submit" disabled={createReading.isPending}>
              {createReading.isPending ? 'Logging…' : 'Log Reading'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete confirmation dialog ────────────────────────────────────────────────

interface DeleteDialogProps {
  reading: SensorReading | null
  onOpenChange: (v: boolean) => void
}

function DeleteDialog({ reading, onOpenChange }: DeleteDialogProps) {
  const deleteReading = useDeleteSensorReading()
  if (!reading) return null
  return (
    <Dialog open={!!reading} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Sensor Reading</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-800">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>
                  This reading is stored in a <strong>TimescaleDB hypertable</strong> and{' '}
                  <strong>cannot be recovered</strong> once deleted.
                </span>
              </div>
              <p>
                Delete <strong>{TYPE_LABEL[reading.sensor_type]}</strong> reading of{' '}
                <strong>{reading.value} {reading.unit}</strong> recorded at{' '}
                {formatDateTime(reading.recorded_at)}?
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={deleteReading.isPending}
            onClick={() =>
              deleteReading.mutate(reading.id, { onSuccess: () => onOpenChange(false) })
            }
          >
            {deleteReading.isPending ? 'Deleting…' : 'Delete Reading'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Summary table (when "all" sensor types selected) ─────────────────────────

interface TypeSummaryProps { readings: SensorReading[] }

function TypeSummaryGrid({ readings }: TypeSummaryProps) {
  const stats = ALL_SENSOR_TYPES.map(type => {
    const rows = readings.filter(r => r.sensor_type === type)
    if (!rows.length) return null
    const values = rows.map(r => r.value)
    const sorted = [...rows].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
    return {
      type,
      count: rows.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      latest: sorted[sorted.length - 1].value,
      unit: rows[0].unit,
      lastSeen: sorted[sorted.length - 1].recorded_at,
    }
  }).filter(Boolean)

  if (!stats.length) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground text-sm">
        No readings in the selected date range
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-xs text-muted-foreground">
            <th className="pb-2 text-left">Sensor Type</th>
            <th className="pb-2 text-right">Readings</th>
            <th className="pb-2 text-right">Latest</th>
            <th className="pb-2 text-right">Avg</th>
            <th className="pb-2 text-right">Min</th>
            <th className="pb-2 text-right">Max</th>
            <th className="pb-2 text-right">Last Seen</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(s => s && (
            <tr key={s.type} className="border-b last:border-0 hover:bg-muted/30">
              <td className="py-2">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block size-2.5 rounded-full"
                    style={{ background: TYPE_COLOR[s.type] }}
                  />
                  {TYPE_LABEL[s.type]}
                </div>
              </td>
              <td className="py-2 text-right font-mono">{s.count}</td>
              <td className="py-2 text-right font-mono font-semibold">
                {s.latest.toFixed(2)} <span className="text-xs text-muted-foreground">{s.unit}</span>
              </td>
              <td className="py-2 text-right font-mono">{s.avg.toFixed(2)}</td>
              <td className="py-2 text-right font-mono text-blue-600">{s.min.toFixed(2)}</td>
              <td className="py-2 text-right font-mono text-orange-600">{s.max.toFixed(2)}</td>
              <td className="py-2 text-right text-xs text-muted-foreground">
                {formatDateTime(s.lastSeen)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Sensors() {
  const [selectedFarmId, setSelectedFarmId] = useState<string | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [selectedType, setSelectedType] = useState<SensorType | 'all'>('all')
  const [logOpen, setLogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<SensorReading | null>(null)

  const now = new Date()
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  const [fromDate, setFromDate] = useState(sevenDaysAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10))

  const { data: farms = [] } = useFarms()
  const { data: fields = [] } = useFields(selectedFarmId)

  const { data: readings = [], isLoading } = useSensorReadings({
    fieldId: selectedFieldId,
    sensorType: selectedType !== 'all' ? selectedType : undefined,
    from: fromDate ? `${fromDate}T00:00:00Z` : undefined,
    to: toDate ? `${toDate}T23:59:59Z` : undefined,
  })

  // Stats
  const stats = useMemo(() => {
    if (!readings.length) return { total: 0, activeSensors: 0, latestAt: null, avgValue: null, unit: '' }
    const sorted = [...readings].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
    const uniqueSensors = new Set(readings.map(r => r.sensor_id ?? `${r.field_id}-${r.sensor_type}`))
    const latestAt = sorted[sorted.length - 1].recorded_at
    const filtered = selectedType !== 'all'
      ? readings.filter(r => r.sensor_type === selectedType)
      : readings
    const avg = filtered.length ? filtered.reduce((a, b) => a + b.value, 0) / filtered.length : null
    const unit = filtered.length ? filtered[0].unit : ''
    return { total: readings.length, activeSensors: uniqueSensors.size, latestAt, avgValue: avg, unit }
  }, [readings, selectedType])

  // Chart data: downsample if too many points
  const chartData = useMemo(() => {
    if (selectedType === 'all') return []
    const sorted = [...readings].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
    const step = sorted.length > 60 ? Math.ceil(sorted.length / 60) : 1
    return sorted
      .filter((_, i) => i % step === 0)
      .map(r => ({ time: formatChartDate(r.recorded_at), value: r.value, unit: r.unit }))
  }, [readings, selectedType])

  const unit = selectedType !== 'all' ? TYPE_UNIT[selectedType] : ''

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sensor Readings</h1>
          <p className="text-sm text-muted-foreground">
            IoT telemetry from field sensors · Readings are immutable once logged
          </p>
        </div>
        <Button onClick={() => setLogOpen(true)}>
          <Plus className="mr-2 size-4" /> Log Reading
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

        <Select
          value={selectedType}
          onValueChange={v => setSelectedType(v as SensorType | 'all')}
        >
          <SelectTrigger className="w-52">
            <SelectValue placeholder="All sensor types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sensor types</SelectItem>
            {ALL_SENSOR_TYPES.map(t => (
              <SelectItem key={t} value={t}>
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block size-2.5 rounded-full"
                    style={{ background: TYPE_COLOR[t] }}
                  />
                  {TYPE_LABEL[t]}
                </div>
              </SelectItem>
            ))}
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
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Activity className="size-4" /> Total Readings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.total.toLocaleString()}</p>
              <p className="mt-1 text-xs text-muted-foreground">In selected range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Cpu className="size-4" /> Active Sensors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.activeSensors}</p>
              <p className="mt-1 text-xs text-muted-foreground">Unique sensor IDs</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Clock className="size-4" /> Latest Reading
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold leading-tight">
                {stats.latestAt ? formatDateTime(stats.latestAt) : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Most recent timestamp</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Zap className="size-4" />
                {selectedType !== 'all' ? TYPE_LABEL[selectedType] : 'Avg Value'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.avgValue !== null ? stats.avgValue.toFixed(2) : '—'}
                {stats.avgValue !== null && (
                  <span className="ml-1 text-base font-normal text-muted-foreground">{stats.unit}</span>
                )}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {selectedType !== 'all' ? 'Period average' : 'Select a type for avg'}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart / Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {selectedType !== 'all'
              ? `${TYPE_LABEL[selectedType]} Over Time`
              : 'Sensor Type Summary'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : selectedType !== 'all' ? (
            chartData.length ? (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 11 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickFormatter={v => `${v}${unit}`}
                    width={56}
                  />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name={`${TYPE_LABEL[selectedType]} (${unit})`}
                    stroke={TYPE_COLOR[selectedType]}
                    strokeWidth={2}
                    dot={chartData.length < 20}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
                No readings for {TYPE_LABEL[selectedType]} in the selected range
              </div>
            )
          ) : (
            <TypeSummaryGrid readings={readings} />
          )}
        </CardContent>
      </Card>

      {/* Readings table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Recent Readings
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              (showing {Math.min(readings.length, 100)} of {readings.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
            </div>
          ) : readings.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground text-sm">
              No sensor readings found
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Recorded At</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Type</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Sensor ID</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Value</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Quality</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {[...readings]
                    .sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))
                    .slice(0, 100)
                    .map(r => (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                          {formatDateTime(r.recorded_at)}
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex items-center gap-1.5">
                            <span
                              className="inline-block size-2 rounded-full"
                              style={{ background: TYPE_COLOR[r.sensor_type] }}
                            />
                            {TYPE_LABEL[r.sensor_type]}
                          </div>
                        </td>
                        <td className="px-4 py-2 font-mono text-xs">
                          {r.sensor_id ?? <span className="text-muted-foreground">—</span>}
                        </td>
                        <td className="px-4 py-2 text-right font-mono font-semibold">
                          {r.value.toFixed(2)}{' '}
                          <span className="text-xs font-normal text-muted-foreground">{r.unit}</span>
                        </td>
                        <td className="px-4 py-2">
                          {r.quality_flag ? (
                            <Badge variant={qualityVariant(r.quality_flag)} className="text-xs">
                              {r.quality_flag}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-right">
                          <Button
                            size="icon"
                            variant="ghost"
                            className="size-7 text-muted-foreground hover:text-destructive"
                            onClick={() => setDeleteTarget(r)}
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <LogReadingDialog open={logOpen} onOpenChange={setLogOpen} />
      <DeleteDialog reading={deleteTarget} onOpenChange={v => { if (!v) setDeleteTarget(null) }} />
    </div>
  )
}
