import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ResponsiveContainer, ComposedChart, LineChart, Line,
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import {
  Plus, Trash2, CloudSun, Filter, Thermometer,
  Droplets, Gauge,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import { useWeather, useCreateWeather, useDeleteWeather } from '@/api/weather'
import { formatDateTime, cn } from '@/lib/utils'
import type { WeatherObservationCreate } from '@/types'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function optNum(s: string): number | undefined {
  return s === '' ? undefined : Number(s)
}

function formatChartDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`
}

function avg(vals: (number | null)[]): number | null {
  const valid = vals.filter((v): v is number => v !== null)
  return valid.length ? valid.reduce((s, v) => s + v, 0) / valid.length : null
}

function sum(vals: (number | null)[]): number {
  return vals.reduce<number>((s, v) => s + (v ?? 0), 0)
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: {
  active?: boolean; payload?: { color: string; name: string; value: number }[]; label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-white p-3 shadow-lg text-xs">
      <p className="font-semibold text-foreground mb-2">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 mb-0.5">
          <div className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground">{p.name}:</span>
          <span className="font-medium">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Form schema ─────────────────────────────────────────────────────────────

const optNumStr = z.string().refine(
  (v) => v === '' || (!isNaN(Number(v))),
  { message: 'Must be a number' },
)

const weatherSchema = z.object({
  field_id: z.string().min(1, 'Please select a field'),
  recorded_at: z.string().min(1, 'Date and time are required'),
  temperature: optNumStr,
  humidity: z.string().refine((v) => v === '' || (Number(v) >= 0 && Number(v) <= 100), {
    message: 'Humidity 0–100%',
  }),
  rainfall: z.string().refine((v) => v === '' || Number(v) >= 0, { message: 'Must be ≥ 0' }),
  wind_speed: z.string().refine((v) => v === '' || Number(v) >= 0, { message: 'Must be ≥ 0' }),
  wind_direction: z.string().refine(
    (v) => v === '' || (Number(v) >= 0 && Number(v) <= 360),
    { message: '0–360°' },
  ),
  solar_radiation: optNumStr,
  atmospheric_pressure: optNumStr,
})

interface WeatherFormValues {
  field_id: string
  recorded_at: string
  temperature: string
  humidity: string
  rainfall: string
  wind_speed: string
  wind_direction: string
  solar_radiation: string
  atmospheric_pressure: string
}

const EMPTY_FORM: WeatherFormValues = {
  field_id: '', recorded_at: '', temperature: '', humidity: '', rainfall: '',
  wind_speed: '', wind_direction: '', solar_radiation: '', atmospheric_pressure: '',
}

// ─── Log Observation Form ─────────────────────────────────────────────────────

interface WeatherFormProps {
  onSubmit: (values: WeatherFormValues) => void
  isPending: boolean
  onCancel: () => void
  preselectedFieldId?: number
  preselectedFarmId?: number
}

function WeatherForm({ onSubmit, isPending, onCancel, preselectedFieldId, preselectedFarmId }: WeatherFormProps) {
  const { data: farms } = useFarms()
  const [formFarmId, setFormFarmId] = useState<number | undefined>(preselectedFarmId)
  const { data: fields } = useFields(formFarmId)

  // Default recorded_at to current datetime-local string
  const nowLocal = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16)

  const { register, handleSubmit, control, formState: { errors } } = useForm<WeatherFormValues>({
    resolver: zodResolver(weatherSchema),
    defaultValues: {
      ...EMPTY_FORM,
      field_id: preselectedFieldId ? String(preselectedFieldId) : '',
      recorded_at: nowLocal,
    },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Farm → Field */}
      {preselectedFieldId ? (
        <div className="space-y-2">
          <Label>Field</Label>
          <div className="flex h-10 items-center rounded-md border bg-muted px-3 text-sm text-muted-foreground">
            {fields?.find((f) => f.id === preselectedFieldId)?.name ?? `Field #${preselectedFieldId}`}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Farm</Label>
            <Select value={formFarmId ? String(formFarmId) : ''} onValueChange={(v) => setFormFarmId(Number(v))}>
              <SelectTrigger><SelectValue placeholder="Select farm…" /></SelectTrigger>
              <SelectContent>
                {farms?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Field *</Label>
            <Controller name="field_id" control={control} render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange} disabled={!formFarmId}>
                <SelectTrigger>
                  <SelectValue placeholder={formFarmId ? 'Select field…' : 'Pick farm first'} />
                </SelectTrigger>
                <SelectContent>
                  {fields?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )} />
            {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
          </div>
        </div>
      )}

      {/* Recorded at */}
      <div className="space-y-2">
        <Label htmlFor="recorded_at">Observed At *</Label>
        <Input id="recorded_at" type="datetime-local" {...register('recorded_at')} />
        {errors.recorded_at && <p className="text-xs text-destructive">{errors.recorded_at.message}</p>}
      </div>

      {/* Temperature + Humidity + Rainfall */}
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-2">
          <Label htmlFor="temperature">Temperature (°C)</Label>
          <Input id="temperature" type="number" step="0.1" placeholder="e.g. 28.5" {...register('temperature')} />
          {errors.temperature && <p className="text-xs text-destructive">{errors.temperature.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="humidity">Humidity (%)</Label>
          <Input id="humidity" type="number" step="0.1" min="0" max="100" placeholder="e.g. 72" {...register('humidity')} />
          {errors.humidity && <p className="text-xs text-destructive">{errors.humidity.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="rainfall">Rainfall (mm)</Label>
          <Input id="rainfall" type="number" step="0.1" min="0" placeholder="e.g. 12.4" {...register('rainfall')} />
          {errors.rainfall && <p className="text-xs text-destructive">{errors.rainfall.message}</p>}
        </div>
      </div>

      {/* Wind speed + direction + pressure + solar */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="wind_speed">Wind Speed (km/h)</Label>
          <Input id="wind_speed" type="number" step="0.1" min="0" placeholder="e.g. 14.2" {...register('wind_speed')} />
          {errors.wind_speed && <p className="text-xs text-destructive">{errors.wind_speed.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="wind_direction">Wind Direction (°)</Label>
          <Input id="wind_direction" type="number" min="0" max="360" placeholder="e.g. 225 = SW" {...register('wind_direction')} />
          {errors.wind_direction && <p className="text-xs text-destructive">{errors.wind_direction.message}</p>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="atmospheric_pressure">Pressure (hPa)</Label>
          <Input id="atmospheric_pressure" type="number" step="0.1" placeholder="e.g. 1013.2" {...register('atmospheric_pressure')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="solar_radiation">Solar Radiation (W/m²)</Label>
          <Input id="solar_radiation" type="number" step="1" min="0" placeholder="e.g. 450" {...register('solar_radiation')} />
        </div>
      </div>

      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>Cancel</Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : 'Log Observation'}
        </Button>
      </DialogFooter>
    </form>
  )
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function WeatherStat({
  label, value, unit, icon: Icon, color, loading,
}: {
  label: string; value: string | number | null; unit?: string
  icon: React.ComponentType<{ className?: string }>; color: string; loading?: boolean
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium text-muted-foreground">{label}</p>
            {loading ? (
              <Skeleton className="mt-1 h-7 w-20" />
            ) : (
              <p className="mt-1 text-2xl font-bold">
                {value != null ? (
                  <>{typeof value === 'number' ? value.toFixed(1) : value}
                    {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
                  </>
                ) : '—'}
              </p>
            )}
          </div>
          <div className={cn('rounded-lg p-2.5', color)}>
            <Icon className="h-4 w-4 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Weather() {
  const { data: farms, isLoading: farmsLoading } = useFarms()
  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [logOpen, setLogOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  // Default date range: last 7 days
  const toDate = new Date().toISOString().split('T')[0]
  const fromDate = new Date(Date.now() - 7 * 86400_000).toISOString().split('T')[0]
  const [from, setFrom] = useState(fromDate)
  const [to, setTo] = useState(toDate)

  const { data: fields } = useFields(selectedFarmId)
  const { data: observations, isLoading, isError } = useWeather({
    fieldId: selectedFieldId,
    from,
    to,
    limit: 200,
  })
  const { mutate: createObs, isPending: creating } = useCreateWeather()
  const { mutate: deleteObs } = useDeleteWeather()

  function handleFarmChange(v: string) {
    setSelectedFarmId(v === 'all' ? undefined : Number(v))
    setSelectedFieldId(undefined)
  }

  function handleCreate(values: {
    field_id: string; recorded_at: string; temperature: string; humidity: string
    rainfall: string; wind_speed: string; wind_direction: string
    solar_radiation: string; atmospheric_pressure: string
  }) {
    const payload: WeatherObservationCreate = {
      field_id: Number(values.field_id),
      recorded_at: new Date(values.recorded_at).toISOString(),
      temperature: optNum(values.temperature),
      humidity: optNum(values.humidity),
      rainfall: optNum(values.rainfall),
      wind_speed: optNum(values.wind_speed),
      wind_direction: optNum(values.wind_direction),
      solar_radiation: optNum(values.solar_radiation),
      atmospheric_pressure: optNum(values.atmospheric_pressure),
    }
    createObs(payload, { onSuccess: () => setLogOpen(false) })
  }

  // Chart data — sorted ascending by recorded_at, downsampled if > 60 points
  const sorted = [...(observations ?? [])].sort(
    (a, b) => a.recorded_at.localeCompare(b.recorded_at),
  )
  const step = sorted.length > 60 ? Math.ceil(sorted.length / 60) : 1
  const chartData = sorted
    .filter((_, i) => i % step === 0)
    .map((o) => ({
      time: formatChartDate(o.recorded_at),
      temp: o.temperature,
      humidity: o.humidity,
      rainfall: o.rainfall,
    }))

  // Stats
  const humidities = observations?.map((o) => o.humidity) ?? []
  const latest = sorted[sorted.length - 1]

  const selectedFarm = farms?.find((f) => f.id === selectedFarmId)
  const selectedField = fields?.find((f) => f.id === selectedFieldId)

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {farmsLoading ? <Skeleton className="h-10 w-44" /> : (
          <Select value={selectedFarmId ? String(selectedFarmId) : 'all'} onValueChange={handleFarmChange}>
            <SelectTrigger className="w-44"><SelectValue placeholder="All farms" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All farms</SelectItem>
              {farms?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
            </SelectContent>
          </Select>
        )}
        {selectedFarmId && (
          <>
            <span className="text-muted-foreground">›</span>
            <Select value={selectedFieldId ? String(selectedFieldId) : 'all'}
              onValueChange={(v) => setSelectedFieldId(v === 'all' ? undefined : Number(v))}>
              <SelectTrigger className="w-44"><SelectValue placeholder="All fields" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All fields</SelectItem>
                {fields?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </>
        )}

        {/* Date range */}
        <div className="flex items-center gap-2 ml-2">
          <span className="text-sm text-muted-foreground">From</span>
          <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="w-36 h-9" />
          <span className="text-sm text-muted-foreground">to</span>
          <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="w-36 h-9" />
        </div>

        <div className="flex-1" />
        <Button onClick={() => setLogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Log Observation
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <WeatherStat label="Latest Temperature" value={latest?.temperature ?? null}
          unit="°C" icon={Thermometer} color="bg-orange-500" loading={isLoading} />
        <WeatherStat label="Avg Humidity" value={avg(humidities)}
          unit="%" icon={Droplets} color="bg-blue-500" loading={isLoading} />
        <WeatherStat label="Total Rainfall" value={observations ? sum(observations.map((o) => o.rainfall)) : null}
          unit="mm" icon={CloudSun} color="bg-cyan-500" loading={isLoading} />
        <WeatherStat label="Latest Pressure" value={latest?.atmospheric_pressure ?? null}
          unit="hPa" icon={Gauge} color="bg-violet-500" loading={isLoading} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Temperature + Humidity */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Temperature & Humidity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-52 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex h-52 items-center justify-center text-sm text-muted-foreground">
                No data in selected period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={210}>
                <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis yAxisId="temp" tick={{ fontSize: 10 }} unit="°C" />
                  <YAxis yAxisId="hum" orientation="right" tick={{ fontSize: 10 }} unit="%" domain={[0, 100]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line yAxisId="temp" type="monotone" dataKey="temp" name="Temp (°C)"
                    stroke="#f97316" strokeWidth={2} dot={false} connectNulls />
                  <Line yAxisId="hum" type="monotone" dataKey="humidity" name="Humidity (%)"
                    stroke="#3b82f6" strokeWidth={2} dot={false} connectNulls strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Rainfall */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Rainfall (mm)</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-52 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex h-52 items-center justify-center text-sm text-muted-foreground">
                No data in selected period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={210}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} unit="mm" />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="rainfall" name="Rainfall (mm)" fill="#06b6d4" opacity={0.8} radius={[2, 2, 0, 0]} />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent observations table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {selectedField
                ? `Observations — ${selectedField.name}`
                : selectedFarm
                ? `Observations — ${selectedFarm.name}`
                : 'All Observations'}
            </CardTitle>
            {observations && (
              <span className="text-xs text-muted-foreground">
                {observations.length} record{observations.length !== 1 ? 's' : ''} in period
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load data. Is the backend running?
            </div>
          ) : observations?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <CloudSun className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No observations in this period</p>
              <p className="text-sm">Adjust the date range or log a new observation.</p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Observed At</TableHead>
                    <TableHead>Field</TableHead>
                    <TableHead>Temp (°C)</TableHead>
                    <TableHead>Humidity (%)</TableHead>
                    <TableHead>Rainfall (mm)</TableHead>
                    <TableHead>Wind (km/h)</TableHead>
                    <TableHead>Pressure (hPa)</TableHead>
                    <TableHead className="text-right">Del</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...(observations ?? [])].reverse().slice(0, 50).map((o) => {
                    const field = fields?.find((f) => f.id === o.field_id)
                    return (
                      <TableRow key={o.id}>
                        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                          {formatDateTime(o.recorded_at)}
                        </TableCell>
                        <TableCell className="text-sm font-medium">
                          {field?.name ?? `Field #${o.field_id}`}
                        </TableCell>
                        <TableCell>
                          {o.temperature != null ? (
                            <span className={cn('font-medium', o.temperature > 35 ? 'text-red-600' : o.temperature < 10 ? 'text-blue-600' : '')}>
                              {o.temperature.toFixed(1)}
                            </span>
                          ) : '—'}
                        </TableCell>
                        <TableCell>{o.humidity != null ? `${o.humidity.toFixed(0)}%` : '—'}</TableCell>
                        <TableCell>
                          {o.rainfall != null && o.rainfall > 0 ? (
                            <span className="font-medium text-cyan-600">{o.rainfall.toFixed(1)}</span>
                          ) : o.rainfall === 0 ? '0' : '—'}
                        </TableCell>
                        <TableCell>{o.wind_speed != null ? o.wind_speed.toFixed(1) : '—'}</TableCell>
                        <TableCell>{o.atmospheric_pressure != null ? o.atmospheric_pressure.toFixed(1) : '—'}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive"
                            onClick={() => setDeleteId(o.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Log observation modal */}
      <Dialog open={logOpen} onOpenChange={setLogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Log Weather Observation</DialogTitle>
            <DialogDescription>Record a weather measurement for a field.</DialogDescription>
          </DialogHeader>
          <WeatherForm
            preselectedFieldId={selectedFieldId}
            preselectedFarmId={selectedFarmId}
            onSubmit={handleCreate}
            isPending={creating}
            onCancel={() => setLogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={deleteId !== null} onOpenChange={(v) => !v && setDeleteId(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete Observation</DialogTitle>
            <DialogDescription>
              Permanently delete this weather record? TimescaleDB rows cannot be recovered once deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive"
              onClick={() => deleteId !== null && deleteObs(deleteId, { onSuccess: () => setDeleteId(null) })}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
