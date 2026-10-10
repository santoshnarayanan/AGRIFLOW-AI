import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Layers, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
import { useFields, useCreateField, useUpdateField, useDeleteField } from '@/api/fields'
import { formatDate } from '@/lib/utils'
import {
  decimalFromApi,
  farmDisplayName,
  formatFarmLocation,
  fieldHasGps,
  formatFieldGps,
} from '@/lib/farm'
import type { Field, FieldCreate, FieldUpdate } from '@/types'

const fieldSchema = z.object({
  farm_id: z.string().min(1, 'Please select a farm'),
  name: z.string().min(1, 'Field name is required').max(255),
  soil_type: z.string().max(50),
  area_hectares: z.string().refine((v) => v === '' || (!isNaN(Number(v)) && Number(v) >= 0), {
    message: 'Area must be zero or greater',
  }),
  latitude: z.string(),
  longitude: z.string(),
})

interface FieldFormValues {
  farm_id: string
  name: string
  soil_type: string
  area_hectares: string
  latitude: string
  longitude: string
}

function fieldPayloadFromForm(values: FieldFormValues): FieldCreate {
  const payload: FieldCreate = { name: values.name.trim() }
  if (values.area_hectares !== '') payload.area_hectares = Number(values.area_hectares)
  if (values.soil_type.trim()) payload.soil_type = values.soil_type.trim()
  if (values.latitude !== '') payload.latitude = Number(values.latitude)
  if (values.longitude !== '') payload.longitude = Number(values.longitude)
  return payload
}

function fieldUpdateFromForm(values: FieldFormValues): FieldUpdate {
  const payload: FieldUpdate = { name: values.name.trim() }
  if (values.area_hectares !== '') payload.area_hectares = Number(values.area_hectares)
  else payload.area_hectares = undefined
  payload.soil_type = values.soil_type.trim() || undefined
  if (values.latitude !== '') payload.latitude = Number(values.latitude)
  if (values.longitude !== '') payload.longitude = Number(values.longitude)
  return payload
}

interface FieldFormProps {
  defaultValues?: Partial<FieldFormValues>
  onSubmit: (values: FieldFormValues) => void
  isPending: boolean
  onCancel: () => void
  mode: 'create' | 'edit'
  lockedFarmId?: string
}

function FieldForm({ defaultValues, onSubmit, isPending, onCancel, mode, lockedFarmId }: FieldFormProps) {
  const { data: farms } = useFarms()

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FieldFormValues>({
    resolver: zodResolver(fieldSchema),
    defaultValues: {
      farm_id: lockedFarmId ?? '',
      name: '',
      soil_type: '',
      area_hectares: '',
      latitude: '',
      longitude: '',
      ...defaultValues,
    },
  })

  const selectedFarmId = watch('farm_id')

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label>Farm *</Label>
        {lockedFarmId ? (
          <div className="flex h-10 items-center rounded-md border border-input bg-muted px-3 text-sm text-muted-foreground">
            {farms?.find((f) => f.id === lockedFarmId)
              ? farmDisplayName(farms.find((f) => f.id === lockedFarmId)!)
              : lockedFarmId}
          </div>
        ) : (
          <>
            <Select
              value={selectedFarmId}
              onValueChange={(v) => setValue('farm_id', v, { shouldValidate: true })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a farm…" />
              </SelectTrigger>
              <SelectContent>
                {farms?.map((farm) => (
                  <SelectItem key={farm.id} value={farm.id}>
                    {farmDisplayName(farm)}
                    {` — ${formatFarmLocation(farm)}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.farm_id && <p className="text-xs text-destructive">{errors.farm_id.message}</p>}
          </>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Field Name *</Label>
        <Input id="name" placeholder="e.g. North Block A" {...register('name')} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="soil_type">Soil Type</Label>
        <Input id="soil_type" placeholder="e.g. Loam" {...register('soil_type')} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="area_hectares">Area (hectares)</Label>
        <Input id="area_hectares" type="number" step="0.01" placeholder="e.g. 12.5" {...register('area_hectares')} />
        {errors.area_hectares && <p className="text-xs text-destructive">{errors.area_hectares.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="latitude">Latitude</Label>
          <Input id="latitude" type="number" step="any" {...register('latitude')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="longitude">Longitude</Label>
          <Input id="longitude" type="number" step="any" {...register('longitude')} />
        </div>
      </div>

      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : mode === 'create' ? 'Create Field' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  )
}

function DeleteFieldDialog({
  field,
  farmName,
  open,
  onClose,
}: {
  field: Field | null
  farmName: string
  open: boolean
  onClose: () => void
}) {
  const { mutate: deleteField, isPending } = useDeleteField()

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Field</DialogTitle>
          <DialogDescription>
            Delete <strong>{field?.name}</strong> from <strong>{farmName}</strong>? This will also
            remove all associated sensor readings, soil profiles, and observation data. This cannot
            be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() => field && deleteField(field.id, { onSuccess: onClose })}
          >
            {isPending ? 'Deleting…' : 'Delete Field'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function Fields() {
  const { data: farms, isLoading: farmsLoading } = useFarms()

  const [selectedFarmId, setSelectedFarmId] = useState<string | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editField, setEditField] = useState<Field | null>(null)
  const [deleteField, setDeleteField] = useState<Field | null>(null)

  const { data: fields, isLoading: fieldsLoading, isError } = useFields(selectedFarmId)
  const { mutate: createField, isPending: creating } = useCreateField()
  const { mutate: updateField, isPending: updating } = useUpdateField()

  const selectedFarm = farms?.find((f) => f.id === selectedFarmId)

  function handleCreate(values: FieldFormValues) {
    createField(
      { farmId: values.farm_id, payload: fieldPayloadFromForm(values) },
      { onSuccess: () => setCreateOpen(false) },
    )
  }

  function handleEdit(values: FieldFormValues) {
    if (!editField) return
    updateField(
      { id: editField.id, payload: fieldUpdateFromForm(values) },
      { onSuccess: () => setEditField(null) },
    )
  }

  const totalArea =
    fields?.reduce((s, f) => s + (decimalFromApi(f.area_hectares) ?? 0), 0) ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">Farm:</span>
        </div>
        {farmsLoading ? (
          <Skeleton className="h-10 w-52" />
        ) : (
          <Select
            value={selectedFarmId ?? 'all'}
            onValueChange={(v) => setSelectedFarmId(v === 'all' ? undefined : v)}
          >
            <SelectTrigger className="w-52">
              <SelectValue placeholder="All farms" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All farms</SelectItem>
              {farms?.map((farm) => (
                <SelectItem key={farm.id} value={farm.id}>
                  {farmDisplayName(farm)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <div className="flex-1" />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Field
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{fields?.length ?? '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {selectedFarm ? `Fields in ${farmDisplayName(selectedFarm)}` : 'Total Fields'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{fields ? totalArea.toFixed(1) : '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Area (ha)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">
              {fields ? fields.filter((f) => fieldHasGps(f)).length : '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">With GPS</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {selectedFarm ? `Fields — ${farmDisplayName(selectedFarm)}` : 'All Fields'}
            </CardTitle>
            {selectedFarm && (
              <Badge variant="outline" className="text-xs">
                {selectedFarm.farm_code}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {fieldsLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load fields. Is the backend running?
            </div>
          ) : fields?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Layers className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No fields yet</p>
              <p className="text-sm">
                {selectedFarm
                  ? `Add the first field to ${farmDisplayName(selectedFarm)}.`
                  : 'Select a farm or click "Add Field" to get started.'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field Name</TableHead>
                  <TableHead>Farm</TableHead>
                  <TableHead>GPS</TableHead>
                  <TableHead>Area</TableHead>
                  <TableHead>Soil</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fields?.map((field) => {
                  const farm = farms?.find((f) => f.id === field.farm_id)
                  return (
                    <TableRow key={field.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{field.name}</p>
                          <p className="text-xs text-muted-foreground truncate max-w-[140px]">{field.id}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm font-medium">
                            {farm ? farmDisplayName(farm) : field.farm_id}
                          </p>
                          {farm && (
                            <p className="text-xs text-muted-foreground">{formatFarmLocation(farm)}</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs max-w-[160px] truncate">
                        {formatFieldGps(field)}
                      </TableCell>
                      <TableCell>
                        {decimalFromApi(field.area_hectares) != null
                          ? `${decimalFromApi(field.area_hectares)} ha`
                          : '—'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{field.soil_type ?? '—'}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatDate(field.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setEditField(field)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteField(field)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Field</DialogTitle>
            <DialogDescription>Register a new field within one of your farms.</DialogDescription>
          </DialogHeader>
          <FieldForm
            mode="create"
            lockedFarmId={selectedFarmId}
            defaultValues={selectedFarmId ? { farm_id: selectedFarmId } : undefined}
            onSubmit={handleCreate}
            isPending={creating}
            onCancel={() => setCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={!!editField} onOpenChange={(v) => !v && setEditField(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Field</DialogTitle>
            <DialogDescription>Update details for {editField?.name}.</DialogDescription>
          </DialogHeader>
          {editField && (
            <FieldForm
              mode="edit"
              lockedFarmId={editField.farm_id}
              defaultValues={{
                farm_id: editField.farm_id,
                name: editField.name,
                soil_type: editField.soil_type ?? '',
                area_hectares:
                  editField.area_hectares != null
                    ? String(decimalFromApi(editField.area_hectares))
                    : '',
                latitude:
                  editField.latitude != null ? String(decimalFromApi(editField.latitude)) : '',
                longitude:
                  editField.longitude != null ? String(decimalFromApi(editField.longitude)) : '',
              }}
              onSubmit={handleEdit}
              isPending={updating}
              onCancel={() => setEditField(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      <DeleteFieldDialog
        field={deleteField}
        farmName={
          farms?.find((f) => f.id === deleteField?.farm_id)
            ? farmDisplayName(farms.find((f) => f.id === deleteField?.farm_id)!)
            : ''
        }
        open={!!deleteField}
        onClose={() => setDeleteField(null)}
      />
    </div>
  )
}
