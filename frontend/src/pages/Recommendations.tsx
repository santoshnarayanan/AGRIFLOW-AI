import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer,
} from 'recharts'
import {
  Lightbulb, Plus, Pencil, Trash2, CheckCircle2, Sparkles, Clock, AlertTriangle,
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
import {
  useRecommendationsForFieldIds,
  useCreateRecommendation,
  useUpdateRecommendation,
  useDeleteRecommendation,
} from '@/api/recommendations'
import { formatDate } from '@/lib/utils'
import type {
  Recommendation,
  RecommendationPriority,
  RecommendationStatus,
  RecommendationType,
} from '@/types'

// ─── Labels & styling ─────────────────────────────────────────────────────────

const ALL_TYPES: RecommendationType[] = [
  'IRRIGATION', 'DISEASE_TREATMENT', 'FERTILIZATION',
  'HARVEST_TIMING', 'SOIL_AMENDMENT', 'GENERAL',
]

const TYPE_LABEL: Record<RecommendationType, string> = {
  IRRIGATION: 'Irrigation',
  DISEASE_TREATMENT: 'Disease treatment',
  FERTILIZATION: 'Fertilization',
  HARVEST_TIMING: 'Harvest timing',
  SOIL_AMENDMENT: 'Soil amendment',
  GENERAL: 'General',
}

const ALL_STATUSES: RecommendationStatus[] = [
  'PENDING', 'ACTIVE', 'ACKNOWLEDGED', 'SUPERSEDED', 'EXPIRED', 'DISMISSED',
]

const STATUS_VARIANT: Record<RecommendationStatus, 'info' | 'success' | 'secondary' | 'warning' | 'destructive' | 'outline'> = {
  PENDING: 'info',
  ACTIVE: 'warning',
  ACKNOWLEDGED: 'success',
  SUPERSEDED: 'secondary',
  EXPIRED: 'outline',
  DISMISSED: 'destructive',
}

const ALL_PRIORITIES: RecommendationPriority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const PRIORITY_CLASS: Record<RecommendationPriority, string> = {
  LOW: 'text-slate-600 bg-slate-100',
  MEDIUM: 'text-blue-700 bg-blue-100',
  HIGH: 'text-orange-700 bg-orange-100',
  CRITICAL: 'text-red-700 bg-red-100',
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
      <p className="font-medium">{payload[0].value} recommendations</p>
    </div>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const formSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  crop_id: z.string().optional(),
  recommendation_type: z.enum([
    'IRRIGATION', 'DISEASE_TREATMENT', 'FERTILIZATION',
    'HARVEST_TIMING', 'SOIL_AMENDMENT', 'GENERAL',
  ]),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
  status: z.enum([
    'PENDING', 'ACTIVE', 'ACKNOWLEDGED', 'SUPERSEDED', 'EXPIRED', 'DISMISSED',
  ]).optional(),
  title: z.string().min(1, 'Title is required').max(255),
  description: z.string().optional(),
  recommended_action: z.string().min(1, 'Action is required'),
  recommended_value: z.string().optional(),
  recommended_unit: z.string().optional(),
  confidence_score: z.string().optional(),
  evidence_summary: z.string().optional(),
  engine_version: z.string().optional(),
  valid_from: z.string().min(1, 'Valid from is required'),
  valid_until: z.string().optional(),
  notes: z.string().optional(),
})

type FormValues = z.infer<typeof formSchema>

// ─── Create / Edit dialog ─────────────────────────────────────────────────────

function RecommendationDialog({
  open,
  onOpenChange,
  editing,
  defaultFieldId,
  defaultFarmId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: Recommendation | null
  defaultFieldId?: string
  defaultFarmId?: string
}) {
  const createRec = useCreateRecommendation()
  const updateRec = useUpdateRecommendation()
  const { data: farms = [] } = useFarms()
  const { data: allFields = [] } = useFields()

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      farm_id: defaultFarmId ?? '',
      field_id: defaultFieldId ?? '',
      crop_id: '',
      recommendation_type: 'GENERAL',
      priority: 'MEDIUM',
      title: '',
      description: '',
      recommended_action: '',
      recommended_value: '',
      recommended_unit: '',
      confidence_score: '',
      evidence_summary: '',
      engine_version: 'manual-ui-v1',
      valid_from: toDatetimeLocal(new Date().toISOString()),
      valid_until: '',
      notes: '',
    },
  })

  const watchFarmId = form.watch('farm_id')
  const watchFieldId = form.watch('field_id')
  const farmFields = useMemo(
    () => allFields.filter((f) => fieldIdStr(f.farm_id) === watchFarmId),
    [allFields, watchFarmId],
  )
  const { data: crops = [] } = useCrops(
    watchFieldId ? Number(watchFieldId) : undefined,
  )

  useEffect(() => {
    if (!open) return
    if (editing) {
      const farm = allFields.find((f) => fieldIdStr(f.id) === editing.field_id)
      form.reset({
        farm_id: farm ? fieldIdStr(farm.farm_id) : '',
        field_id: editing.field_id,
        crop_id: editing.crop_id ?? '',
        recommendation_type: editing.recommendation_type,
        priority: editing.priority,
        status: editing.status,
        title: editing.title,
        description: editing.description ?? '',
        recommended_action: editing.recommended_action,
        recommended_value: editing.recommended_value != null ? String(editing.recommended_value) : '',
        recommended_unit: editing.recommended_unit ?? '',
        confidence_score: editing.confidence_score != null ? String(editing.confidence_score) : '',
        evidence_summary: editing.evidence_summary ?? '',
        engine_version: editing.engine_version ?? '',
        valid_from: toDatetimeLocal(editing.valid_from),
        valid_until: editing.valid_until ? toDatetimeLocal(editing.valid_until) : '',
        notes: editing.notes ?? '',
      })
    } else {
      form.reset({
        farm_id: defaultFarmId ?? '',
        field_id: defaultFieldId ?? '',
        crop_id: '',
        recommendation_type: 'GENERAL',
        priority: 'MEDIUM',
        title: '',
        description: '',
        recommended_action: '',
        recommended_value: '',
        recommended_unit: '',
        confidence_score: '',
        evidence_summary: '',
        engine_version: 'manual-ui-v1',
        valid_from: toDatetimeLocal(new Date().toISOString()),
        valid_until: '',
        notes: '',
      })
    }
  }, [open, editing, form, allFields, defaultFarmId, defaultFieldId])

  const isPending = createRec.isPending || updateRec.isPending

  function onSubmit(values: FormValues) {
    const confidence = values.confidence_score
      ? Number.parseFloat(values.confidence_score)
      : undefined
    const recValue = values.recommended_value
      ? Number.parseFloat(values.recommended_value)
      : undefined

    if (editing) {
      updateRec.mutate(
        {
          id: editing.id,
          payload: {
            status: values.status,
            priority: values.priority,
            title: values.title,
            description: values.description || null,
            recommended_action: values.recommended_action,
            recommended_value: recValue ?? null,
            recommended_unit: values.recommended_unit || null,
            confidence_score: confidence ?? null,
            evidence_summary: values.evidence_summary || null,
            valid_until: values.valid_until ? datetimeLocalToIso(values.valid_until) : null,
            notes: values.notes || null,
          },
        },
        { onSuccess: () => onOpenChange(false) },
      )
      return
    }

    createRec.mutate(
      {
        fieldId: values.field_id,
        payload: {
          crop_id: values.crop_id || null,
          recommendation_type: values.recommendation_type,
          priority: values.priority,
          title: values.title,
          description: values.description || null,
          recommended_action: values.recommended_action,
          recommended_value: recValue ?? null,
          recommended_unit: values.recommended_unit || null,
          confidence_score: confidence ?? null,
          evidence_summary: values.evidence_summary || null,
          engine_version: values.engine_version || null,
          valid_from: datetimeLocalToIso(values.valid_from),
          valid_until: values.valid_until ? datetimeLocalToIso(values.valid_until) : null,
          notes: values.notes || null,
        },
      },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit recommendation' : 'New recommendation'}</DialogTitle>
          <DialogDescription>
            Structured agronomic decision record — maps to Phase 13 Recommendation API.
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
                      form.setValue('crop_id', '')
                    }}
                    disabled={!!editing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select farm" />
                    </SelectTrigger>
                    <SelectContent>
                      {farms.map((f) => (
                        <SelectItem key={f.id} value={fieldIdStr(f.id)}>
                          {(f as { name?: string; farm_name?: string }).farm_name
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
                    onValueChange={(v) => {
                      field.onChange(v)
                      form.setValue('crop_id', '')
                    }}
                    disabled={!!editing || !watchFarmId}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select field" />
                    </SelectTrigger>
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

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Controller
                name="recommendation_type"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
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
              <Label>Priority</Label>
              <Controller
                name="priority"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ALL_PRIORITIES.map((p) => (
                        <SelectItem key={p} value={p}>{p}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            {editing && (
              <div className="space-y-2">
                <Label>Status</Label>
                <Controller
                  name="status"
                  control={form.control}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {ALL_STATUSES.map((s) => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label>Crop (optional)</Label>
            <Controller
              name="crop_id"
              control={form.control}
              render={({ field }) => (
                <Select
                  value={field.value || 'none'}
                  onValueChange={(v) => field.onChange(v === 'none' ? '' : v)}
                  disabled={!watchFieldId}
                >
                  <SelectTrigger><SelectValue placeholder="Field-level only" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None (field-level)</SelectItem>
                    {crops.map((c) => (
                      <SelectItem key={c.id} value={fieldIdStr(c.id)}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Title</Label>
            <Input {...form.register('title')} />
            {form.formState.errors.title && (
              <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Recommended action</Label>
            <Textarea rows={2} {...form.register('recommended_action')} />
          </div>

          <div className="space-y-2">
            <Label>Description / rationale</Label>
            <Textarea rows={2} {...form.register('description')} />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Value</Label>
              <Input type="number" step="any" placeholder="e.g. 25" {...form.register('recommended_value')} />
            </div>
            <div className="space-y-2">
              <Label>Unit</Label>
              <Input placeholder="L/m², kg/ha…" {...form.register('recommended_unit')} />
            </div>
            <div className="space-y-2">
              <Label>Confidence (0–1)</Label>
              <Input type="number" step="0.001" min={0} max={1} {...form.register('confidence_score')} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Valid from</Label>
              <Input type="datetime-local" {...form.register('valid_from')} />
            </div>
            <div className="space-y-2">
              <Label>Valid until (optional)</Label>
              <Input type="datetime-local" {...form.register('valid_until')} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Evidence summary</Label>
            <Textarea rows={2} {...form.register('evidence_summary')} />
          </div>

          {!editing && (
            <div className="space-y-2">
              <Label>Engine version</Label>
              <Input {...form.register('engine_version')} />
            </div>
          )}

          <div className="space-y-2">
            <Label>Operator notes</Label>
            <Textarea rows={2} {...form.register('notes')} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {editing ? 'Save changes' : 'Create recommendation'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete dialog ────────────────────────────────────────────────────────────

function DeleteDialog({
  target,
  onClose,
}: {
  target: Recommendation | null
  onClose: () => void
}) {
  const { mutate, isPending } = useDeleteRecommendation()

  return (
    <Dialog open={!!target} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete recommendation?</DialogTitle>
          <DialogDescription>
            Permanently removes &quot;{target?.title}&quot;. Linked alerts keep their history but
            lose the recommendation reference (SET NULL).
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() => {
              if (!target) return
              mutate(target.id, { onSuccess: onClose })
            }}
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Recommendations() {
  const [selectedFarmId, setSelectedFarmId] = useState<string | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<string | undefined>()
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Recommendation | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Recommendation | null>(null)

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

  const { data: recommendations = [], isLoading } = useRecommendationsForFieldIds(
    fieldIdsToLoad.length > 0 ? fieldIdsToLoad : [],
  )

  const updateRec = useUpdateRecommendation()

  const filtered = useMemo(() => {
    return recommendations.filter((r) => {
      if (statusFilter !== 'all' && r.status !== statusFilter) return false
      if (typeFilter !== 'all' && r.recommendation_type !== typeFilter) return false
      return true
    })
  }, [recommendations, statusFilter, typeFilter])

  const stats = useMemo(() => {
    const active = filtered.filter((r) => r.status === 'ACTIVE').length
    const pending = filtered.filter((r) => r.status === 'PENDING').length
    const withConf = filtered.filter((r) => r.confidence_score != null)
    const avgConf = withConf.length
      ? withConf.reduce((s, r) => s + (r.confidence_score ?? 0), 0) / withConf.length
      : null
    return { total: filtered.length, active, pending, avgConf }
  }, [filtered])

  const chartData = useMemo(() => {
    const counts: Record<string, number> = {}
    ALL_TYPES.forEach((t) => { counts[t] = 0 })
    filtered.forEach((r) => { counts[r.recommendation_type] = (counts[r.recommendation_type] ?? 0) + 1 })
    return ALL_TYPES.map((t) => ({
      type: TYPE_LABEL[t],
      count: counts[t],
    }))
  }, [filtered])

  const fieldNameById = useMemo(() => {
    const m = new Map<string, string>()
    allFields.forEach((f) => m.set(fieldIdStr(f.id), f.name))
    return m
  }, [allFields])

  function openCreate() {
    setEditing(null)
    setDialogOpen(true)
  }

  function openEdit(rec: Recommendation) {
    setEditing(rec)
    setDialogOpen(true)
  }

  function acknowledge(rec: Recommendation) {
    updateRec.mutate({ id: rec.id, payload: { status: 'ACKNOWLEDGED' } })
  }

  function activate(rec: Recommendation) {
    updateRec.mutate({ id: rec.id, payload: { status: 'ACTIVE' } })
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
          <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
          <p className="text-sm text-muted-foreground">
            AI and operator decision queue · validity windows and lifecycle status
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 size-4" /> New recommendation
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select
          value={selectedFarmId ?? 'all'}
          onValueChange={(v) => {
            setSelectedFarmId(v === 'all' ? undefined : v)
            setSelectedFieldId(undefined)
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All farms" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All farms</SelectItem>
            {farms.map((f) => (
              <SelectItem key={f.id} value={fieldIdStr(f.id)}>
                {farmName(f.id)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={selectedFieldId ?? 'all'}
          onValueChange={(v) => setSelectedFieldId(v === 'all' ? undefined : v)}
          disabled={!selectedFarmId}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder={selectedFarmId ? 'All fields' : 'Select farm first'} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All fields in farm</SelectItem>
            {fieldsInFarm.map((f) => (
              <SelectItem key={f.id} value={fieldIdStr(f.id)}>{f.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {ALL_STATUSES.map((s) => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {ALL_TYPES.map((t) => (
              <SelectItem key={t} value={t}>{TYPE_LABEL[t]}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-blue-500 p-3"><Lightbulb className="size-5 text-white" /></div>
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
            <div className="rounded-lg bg-amber-500 p-3"><Clock className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Active queue</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">{stats.active}</p>
              )}
              <p className="text-xs text-muted-foreground">{stats.pending} pending</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-violet-500 p-3"><Sparkles className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Avg confidence</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-16" /> : (
                <p className="text-2xl font-bold">
                  {stats.avgConf != null ? stats.avgConf.toFixed(3) : '—'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-green-600 p-3"><CheckCircle2 className="size-5 text-white" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Acknowledged</p>
              {isLoading ? <Skeleton className="mt-1 h-8 w-12" /> : (
                <p className="text-2xl font-bold">
                  {filtered.filter((r) => r.status === 'ACKNOWLEDGED').length}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">By type</CardTitle>
          </CardHeader>
          <CardContent className="h-56">
            {isLoading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="type" tick={{ fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={50} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Bar dataKey="count" fill="hsl(142.1 76.2% 36.3%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Recommendation log</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="space-y-2 p-6">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <AlertTriangle className="mb-2 size-8 opacity-30" />
                <p className="text-sm">No recommendations match the current filters</p>
              </div>
            ) : (
              <div className="max-h-[28rem] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Field</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead>Valid</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.map((rec) => (
                      <TableRow key={rec.id}>
                        <TableCell>
                          <div className="max-w-[200px]">
                            <p className="font-medium truncate">{rec.title}</p>
                            <p className="text-xs text-muted-foreground truncate">{rec.recommended_action}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {fieldNameById.get(rec.field_id) ?? rec.field_id.slice(0, 8)}
                        </TableCell>
                        <TableCell className="text-xs">{TYPE_LABEL[rec.recommendation_type]}</TableCell>
                        <TableCell>
                          <Badge variant={STATUS_VARIANT[rec.status]}>{rec.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className={`rounded px-2 py-0.5 text-xs font-medium ${PRIORITY_CLASS[rec.priority]}`}>
                            {rec.priority}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm tabular-nums">
                          {rec.confidence_score != null
                            ? Number(rec.confidence_score).toFixed(3)
                            : '—'}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                          {formatDate(rec.valid_from)}
                          {rec.valid_until ? ` → ${formatDate(rec.valid_until)}` : ''}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {rec.status === 'PENDING' && (
                              <Button size="icon" variant="ghost" title="Activate" onClick={() => activate(rec)}>
                                <Sparkles className="size-4" />
                              </Button>
                            )}
                            {(rec.status === 'ACTIVE' || rec.status === 'PENDING') && (
                              <Button size="icon" variant="ghost" title="Acknowledge" onClick={() => acknowledge(rec)}>
                                <CheckCircle2 className="size-4 text-green-600" />
                              </Button>
                            )}
                            <Button size="icon" variant="ghost" onClick={() => openEdit(rec)}>
                              <Pencil className="size-4" />
                            </Button>
                            <Button size="icon" variant="ghost" onClick={() => setDeleteTarget(rec)}>
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

      <RecommendationDialog
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
