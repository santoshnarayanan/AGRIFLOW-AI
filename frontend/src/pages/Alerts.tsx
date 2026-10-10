import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer,
} from 'recharts'
import {
  BellRing, Plus, Pencil, Trash2, CheckCircle2, AlertTriangle,
} from 'lucide-react'
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
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import { useCrops } from '@/api/crops'
import { useFieldRecommendations } from '@/api/recommendations'
import {
  useAlertsForFieldIds,
  useCreateAlert,
  useUpdateAlert,
  useDeleteAlert,
} from '@/api/alerts'
import { formatDateTime } from '@/lib/utils'
import type { Alert, AlertSeverity, AlertType } from '@/types'

const ALL_TYPES: AlertType[] = [
  'SOIL_MOISTURE_LOW', 'SOIL_MOISTURE_HIGH', 'DISEASE_RISK_HIGH', 'DISEASE_OUTBREAK',
  'FROST_RISK', 'HEAT_STRESS', 'DROUGHT_STRESS', 'SENSOR_ANOMALY',
  'IRRIGATION_OVERDUE', 'HARVEST_WINDOW_OPEN',
]

const TYPE_LABEL: Record<AlertType, string> = {
  SOIL_MOISTURE_LOW: 'Soil moisture low',
  SOIL_MOISTURE_HIGH: 'Soil moisture high',
  DISEASE_RISK_HIGH: 'Disease risk high',
  DISEASE_OUTBREAK: 'Disease outbreak',
  FROST_RISK: 'Frost risk',
  HEAT_STRESS: 'Heat stress',
  DROUGHT_STRESS: 'Drought stress',
  SENSOR_ANOMALY: 'Sensor anomaly',
  IRRIGATION_OVERDUE: 'Irrigation overdue',
  HARVEST_WINDOW_OPEN: 'Harvest window open',
}

const ALL_SEVERITIES: AlertSeverity[] = ['INFO', 'WARNING', 'HIGH', 'CRITICAL']

const SEVERITY_VARIANT: Record<AlertSeverity, 'info' | 'warning' | 'destructive' | 'critical'> = {
  INFO: 'info',
  WARNING: 'warning',
  HIGH: 'destructive',
  CRITICAL: 'critical',
}

function fieldIdStr(id: number | string): string {
  return String(id)
}

function toDatetimeLocal(iso: string) {
  const d = new Date(iso)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

function datetimeLocalToIso(local: string): string {
  return new Date(local).toISOString()
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value?: number }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-1 text-xs font-medium text-muted-foreground">{label}</p>
      <p className="font-medium">{payload[0].value} alerts</p>
    </div>
  )
}

const formSchema = z.object({
  farm_id: z.string().min(1),
  field_id: z.string().min(1),
  crop_id: z.string().optional(),
  recommendation_id: z.string().optional(),
  alert_type: z.enum([
    'SOIL_MOISTURE_LOW', 'SOIL_MOISTURE_HIGH', 'DISEASE_RISK_HIGH', 'DISEASE_OUTBREAK',
    'FROST_RISK', 'HEAT_STRESS', 'DROUGHT_STRESS', 'SENSOR_ANOMALY',
    'IRRIGATION_OVERDUE', 'HARVEST_WINDOW_OPEN',
  ]),
  severity: z.enum(['INFO', 'WARNING', 'HIGH', 'CRITICAL']),
  title: z.string().min(1).max(255),
  message: z.string().min(1),
  triggered_at: z.string().min(1),
  expires_at: z.string().optional(),
  source_metric: z.string().optional(),
  source_value: z.string().optional(),
  threshold_value: z.string().optional(),
  is_acknowledged: z.boolean().optional(),
})

type FormValues = z.infer<typeof formSchema>

function AlertDialog({
  open,
  onOpenChange,
  editing,
  defaultFieldId,
  defaultFarmId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: Alert | null
  defaultFieldId?: string
  defaultFarmId?: string
}) {
  const createAlert = useCreateAlert()
  const updateAlert = useUpdateAlert()
  const { data: farms = [] } = useFarms()
  const { data: allFields = [] } = useFields()

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      farm_id: '',
      field_id: '',
      alert_type: 'SOIL_MOISTURE_LOW',
      severity: 'WARNING',
      title: '',
      message: '',
      triggered_at: toDatetimeLocal(new Date().toISOString()),
      expires_at: '',
    },
  })

  const watchFarmId = form.watch('farm_id')
  const watchFieldId = form.watch('field_id')
  const farmFields = useMemo(
    () => allFields.filter((f) => fieldIdStr(f.farm_id) === watchFarmId),
    [allFields, watchFarmId],
  )
  const { data: crops = [] } = useCrops(watchFieldId ? Number(watchFieldId) : undefined)
  const { data: fieldRecs = [] } = useFieldRecommendations(watchFieldId || undefined)

  useEffect(() => {
    if (!open) return
    if (editing) {
      const farm = allFields.find((f) => fieldIdStr(f.id) === editing.field_id)
      form.reset({
        farm_id: farm ? fieldIdStr(farm.farm_id) : '',
        field_id: editing.field_id,
        crop_id: editing.crop_id ?? '',
        recommendation_id: editing.recommendation_id ?? '',
        alert_type: editing.alert_type,
        severity: editing.severity,
        title: editing.title,
        message: editing.message,
        triggered_at: toDatetimeLocal(editing.triggered_at),
        expires_at: editing.expires_at ? toDatetimeLocal(editing.expires_at) : '',
        source_metric: editing.source_metric ?? '',
        source_value: editing.source_value != null ? String(editing.source_value) : '',
        threshold_value: editing.threshold_value != null ? String(editing.threshold_value) : '',
        is_acknowledged: editing.is_acknowledged,
      })
    } else {
      form.reset({
        farm_id: defaultFarmId ?? '',
        field_id: defaultFieldId ?? '',
        crop_id: '',
        recommendation_id: '',
        alert_type: 'SOIL_MOISTURE_LOW',
        severity: 'WARNING',
        title: '',
        message: '',
        triggered_at: toDatetimeLocal(new Date().toISOString()),
        expires_at: '',
        source_metric: '',
        source_value: '',
        threshold_value: '',
      })
    }
  }, [open, editing, form, allFields, defaultFarmId, defaultFieldId])

  const isPending = createAlert.isPending || updateAlert.isPending

  function onSubmit(values: FormValues) {
    const srcVal = values.source_value ? Number.parseFloat(values.source_value) : undefined
    const thresh = values.threshold_value ? Number.parseFloat(values.threshold_value) : undefined

    if (editing) {
      updateAlert.mutate(
        {
          id: editing.id,
          payload: {
            severity: values.severity,
            title: values.title,
            message: values.message,
            is_acknowledged: values.is_acknowledged,
            expires_at: values.expires_at ? datetimeLocalToIso(values.expires_at) : null,
          },
        },
        { onSuccess: () => onOpenChange(false) },
      )
      return
    }

    createAlert.mutate(
      {
        fieldId: values.field_id,
        payload: {
          crop_id: values.crop_id || null,
          recommendation_id: values.recommendation_id || null,
          alert_type: values.alert_type,
          severity: values.severity,
          title: values.title,
          message: values.message,
          triggered_at: datetimeLocalToIso(values.triggered_at),
          expires_at: values.expires_at ? datetimeLocalToIso(values.expires_at) : null,
          source_metric: values.source_metric || null,
          source_value: srcVal ?? null,
          threshold_value: thresh ?? null,
        },
      },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit alert' : 'Raise alert'}</DialogTitle>
          <DialogDescription>
            Operational alert tied to a field; optional crop and recommendation context.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Farm</Label>
              <Controller
                name="farm_id"
                control={form.control}
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={(v) => {
                      field.onChange(v)
                      form.setValue('field_id', '')
                    }}
                    disabled={!!editing}
                  >
                    <SelectTrigger><SelectValue placeholder="Select farm" /></SelectTrigger>
                    <SelectContent>
                      {farms.map((f) => (
                        <SelectItem key={f.id} value={fieldIdStr(f.id)}>
                          {(f as { farm_name?: string; name?: string }).farm_name
                            ?? (f as { name?: string }).name
                            ?? `Farm ${f.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label>Field</Label>
              <Controller
                name="field_id"
                control={form.control}
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={!!editing || !watchFarmId}
                  >
                    <SelectTrigger><SelectValue placeholder="Select field" /></SelectTrigger>
                    <SelectContent>
                      {farmFields.map((f) => (
                        <SelectItem key={f.id} value={fieldIdStr(f.id)}>{f.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Alert type</Label>
              <Controller
                name="alert_type"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange} disabled={!!editing}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ALL_TYPES.map((t) => (
                        <SelectItem key={t} value={t}>{TYPE_LABEL[t]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label>Severity</Label>
              <Controller
                name="severity"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ALL_SEVERITIES.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Crop (optional)</Label>
              <Controller
                name="crop_id"
                control={form.control}
                render={({ field }) => (
                  <Select
                    value={field.value || 'none'}
                    onValueChange={(v) => field.onChange(v === 'none' ? '' : v)}
                    disabled={!watchFieldId || !!editing}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {crops.map((c) => (
                        <SelectItem key={c.id} value={fieldIdStr(c.id)}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label>Linked recommendation (optional)</Label>
              <Controller
                name="recommendation_id"
                control={form.control}
                render={({ field }) => (
                  <Select
                    value={field.value || 'none'}
                    onValueChange={(v) => field.onChange(v === 'none' ? '' : v)}
                    disabled={!watchFieldId || !!editing}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {fieldRecs.map((r) => (
                        <SelectItem key={r.id} value={r.id}>{r.title}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Title</Label>
            <Input {...form.register('title')} />
          </div>
          <div className="space-y-2">
            <Label>Message</Label>
            <Textarea rows={3} {...form.register('message')} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Triggered at</Label>
              <Input type="datetime-local" {...form.register('triggered_at')} disabled={!!editing} />
            </div>
            <div className="space-y-2">
              <Label>Expires at (optional)</Label>
              <Input type="datetime-local" {...form.register('expires_at')} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Source metric</Label>
              <Input placeholder="soil_moisture_pct" {...form.register('source_metric')} disabled={!!editing} />
            </div>
            <div className="space-y-2">
              <Label>Source value</Label>
              <Input type="number" step="any" {...form.register('source_value')} disabled={!!editing} />
            </div>
            <div className="space-y-2">
              <Label>Threshold</Label>
              <Input type="number" step="any" {...form.register('threshold_value')} disabled={!!editing} />
            </div>
          </div>

          {editing && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="ack"
                checked={form.watch('is_acknowledged') ?? false}
                onChange={(e) => form.setValue('is_acknowledged', e.target.checked)}
              />
              <Label htmlFor="ack">Acknowledged</Label>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending}>
              {editing ? 'Save' : 'Create alert'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function DeleteDialog({
  target,
  onClose,
}: {
  target: Alert | null
  onClose: () => void
}) {
  const { mutate, isPending } = useDeleteAlert()
  return (
    <Dialog open={!!target} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete alert?</DialogTitle>
          <DialogDescription>
            Permanently removes &quot;{target?.title}&quot;.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() => target && mutate(target.id, { onSuccess: onClose })}
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function Alerts() {
  const [selectedFarmId, setSelectedFarmId] = useState<string | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<string | undefined>()
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [activeOnly, setActiveOnly] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Alert | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Alert | null>(null)

  const { data: farms = [] } = useFarms()
  const { data: fieldsInFarm = [] } = useFields(
    selectedFarmId ? Number(selectedFarmId) : undefined,
  )
  const { data: allFields = [] } = useFields()

  const fieldIdsToLoad = useMemo(() => {
    if (selectedFieldId) return [selectedFieldId]
    if (selectedFarmId) return fieldsInFarm.map((f) => fieldIdStr(f.id))
    return allFields.map((f) => fieldIdStr(f.id))
  }, [selectedFieldId, selectedFarmId, fieldsInFarm, allFields])

  const { data: alerts = [], isLoading } = useAlertsForFieldIds(
    fieldIdsToLoad.length > 0 ? fieldIdsToLoad : [],
    activeOnly,
  )

  const updateAlert = useUpdateAlert()

  const filtered = useMemo(() => {
    return alerts.filter((a) => {
      if (severityFilter !== 'all' && a.severity !== severityFilter) return false
      if (typeFilter !== 'all' && a.alert_type !== typeFilter) return false
      return true
    })
  }, [alerts, severityFilter, typeFilter])

  const stats = useMemo(() => {
    const unack = filtered.filter((a) => !a.is_acknowledged).length
    const critical = filtered.filter((a) => a.severity === 'CRITICAL' && !a.is_acknowledged).length
    const high = filtered.filter((a) => a.severity === 'HIGH' && !a.is_acknowledged).length
    return { total: filtered.length, unack, critical, high }
  }, [filtered])

  const chartData = useMemo(() => {
    const counts: Record<AlertSeverity, number> = {
      INFO: 0, WARNING: 0, HIGH: 0, CRITICAL: 0,
    }
    filtered.filter((a) => !a.is_acknowledged).forEach((a) => { counts[a.severity]++ })
    return ALL_SEVERITIES.map((s) => ({ severity: s, count: counts[s] }))
  }, [filtered])

  const fieldNameById = useMemo(() => {
    const m = new Map<string, string>()
    allFields.forEach((f) => m.set(fieldIdStr(f.id), f.name))
    return m
  }, [allFields])

  function acknowledge(alert: Alert) {
    updateAlert.mutate({ id: alert.id, payload: { is_acknowledged: true } })
  }

  const farmName = (id: number | string) => {
    const f = farms.find((x) => fieldIdStr(x.id) === fieldIdStr(id))
    return (f as { farm_name?: string; name?: string })?.farm_name
      ?? (f as { name?: string })?.name
      ?? 'Farm'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Alerts</h1>
          <p className="text-sm text-muted-foreground">
            Operational conditions requiring attention · acknowledge to clear the active queue
          </p>
        </div>
        <Button onClick={() => { setEditing(null); setDialogOpen(true) }}>
          <Plus className="mr-2 size-4" /> Raise alert
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={selectedFarmId ?? 'all'}
          onValueChange={(v) => {
            setSelectedFarmId(v === 'all' ? undefined : v)
            setSelectedFieldId(undefined)
          }}
        >
          <SelectTrigger className="w-44"><SelectValue placeholder="All farms" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All farms</SelectItem>
            {farms.map((f) => (
              <SelectItem key={f.id} value={fieldIdStr(f.id)}>{farmName(f.id)}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={selectedFieldId ?? 'all'}
          onValueChange={(v) => setSelectedFieldId(v === 'all' ? undefined : v)}
          disabled={!selectedFarmId}
        >
          <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All fields in farm</SelectItem>
            {fieldsInFarm.map((f) => (
              <SelectItem key={f.id} value={fieldIdStr(f.id)}>{f.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            {ALL_SEVERITIES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {ALL_TYPES.map((t) => <SelectItem key={t} value={t}>{TYPE_LABEL[t]}</SelectItem>)}
          </SelectContent>
        </Select>

        <Button
          variant={activeOnly ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveOnly((v) => !v)}
        >
          {activeOnly ? 'Unacknowledged only' : 'All alerts'}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-amber-500 p-3"><BellRing className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">In scope</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">{stats.total}</p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-orange-500 p-3"><AlertTriangle className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Unacknowledged</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">{stats.unack}</p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-red-600 p-3"><AlertTriangle className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Critical (active)</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">{stats.critical}</p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-red-400 p-3"><CheckCircle2 className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">High (active)</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">{stats.high}</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Active by severity</CardTitle>
          </CardHeader>
          <CardContent className="h-56">
            {isLoading ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="severity" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Alert log</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="space-y-2 p-6">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <CheckCircle2 className="mb-2 size-8 opacity-30" />
                <p className="text-sm">No alerts match filters</p>
              </div>
            ) : (
              <div className="max-h-[28rem] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Field</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Triggered</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.map((alert) => (
                      <TableRow key={alert.id}>
                        <TableCell>
                          <div className="max-w-[180px]">
                            <p className="font-medium truncate">{alert.title}</p>
                            <p className="text-xs text-muted-foreground truncate">{alert.message}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {fieldNameById.get(alert.field_id) ?? alert.field_id.slice(0, 8)}
                        </TableCell>
                        <TableCell className="text-xs">{TYPE_LABEL[alert.alert_type]}</TableCell>
                        <TableCell>
                          <Badge variant={SEVERITY_VARIANT[alert.severity]}>{alert.severity}</Badge>
                        </TableCell>
                        <TableCell className="text-xs whitespace-nowrap text-muted-foreground">
                          {formatDateTime(alert.triggered_at)}
                        </TableCell>
                        <TableCell>
                          {alert.is_acknowledged ? (
                            <Badge variant="success">Ack</Badge>
                          ) : (
                            <Badge variant="warning">Open</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {!alert.is_acknowledged && (
                              <Button size="icon" variant="ghost" title="Acknowledge" onClick={() => acknowledge(alert)}>
                                <CheckCircle2 className="size-4 text-green-600" />
                              </Button>
                            )}
                            <Button size="icon" variant="ghost" onClick={() => { setEditing(alert); setDialogOpen(true) }}>
                              <Pencil className="size-4" />
                            </Button>
                            <Button size="icon" variant="ghost" onClick={() => setDeleteTarget(alert)}>
                              <Trash2 className="size-4 text-destructive" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <AlertDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        defaultFieldId={selectedFieldId}
        defaultFarmId={selectedFarmId}
      />
      <DeleteDialog target={deleteTarget} onClose={() => setDeleteTarget(null)} />
    </div>
  )
}
