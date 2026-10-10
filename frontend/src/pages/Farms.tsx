import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Tractor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useFarms, useCreateFarm, useUpdateFarm, useDeleteFarm } from '@/api/farms'
import { formatDate } from '@/lib/utils'
import { decimalFromApi, formatFarmLocation, farmDisplayName } from '@/lib/farm'
import type { Farm, FarmCreate, FarmUpdate } from '@/types'

const coord = z.string().refine((v) => v !== '' && !isNaN(Number(v)), { message: 'Required' })
const positiveArea = z.string().refine((v) => v !== '' && !isNaN(Number(v)) && Number(v) > 0, {
  message: 'Area must be greater than zero',
})

const farmCreateSchema = z.object({
  farm_code: z.string().min(1, 'Farm code is required').max(50),
  farm_name: z.string().min(1, 'Farm name is required').max(255),
  owner_name: z.string().min(1, 'Owner name is required').max(255),
  country: z.string().min(1, 'Country is required').max(100),
  state: z.string().min(1, 'State is required').max(100),
  city: z.string().min(1, 'City is required').max(100),
  latitude: coord,
  longitude: coord,
  total_area_hectares: positiveArea,
})

const farmEditSchema = farmCreateSchema.omit({ farm_code: true })

type FarmCreateFormValues = z.infer<typeof farmCreateSchema>
type FarmEditFormValues = z.infer<typeof farmEditSchema>

function toCreatePayload(values: FarmCreateFormValues): FarmCreate {
  return {
    farm_code: values.farm_code.trim(),
    farm_name: values.farm_name.trim(),
    owner_name: values.owner_name.trim(),
    country: values.country.trim(),
    state: values.state.trim(),
    city: values.city.trim(),
    latitude: Number(values.latitude),
    longitude: Number(values.longitude),
    total_area_hectares: Number(values.total_area_hectares),
    is_active: true,
  }
}

function toUpdatePayload(values: FarmEditFormValues): FarmUpdate {
  return {
    farm_name: values.farm_name.trim(),
    owner_name: values.owner_name.trim(),
    country: values.country.trim(),
    state: values.state.trim(),
    city: values.city.trim(),
    latitude: Number(values.latitude),
    longitude: Number(values.longitude),
    total_area_hectares: Number(values.total_area_hectares),
  }
}

function FarmCreateForm({
  defaultValues,
  onSubmit,
  isPending,
  onCancel,
}: {
  defaultValues?: Partial<FarmCreateFormValues>
  onSubmit: (values: FarmCreateFormValues) => void
  isPending: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FarmCreateFormValues>({
    resolver: zodResolver(farmCreateSchema),
    defaultValues: {
      farm_code: '',
      farm_name: '',
      owner_name: '',
      country: '',
      state: '',
      city: '',
      latitude: '',
      longitude: '',
      total_area_hectares: '',
      ...defaultValues,
    },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
      <div className="space-y-2">
        <Label htmlFor="farm_code">Farm Code *</Label>
        <Input id="farm_code" placeholder="e.g. FARM-001" {...register('farm_code')} />
        {errors.farm_code && <p className="text-xs text-destructive">{errors.farm_code.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="farm_name">Farm Name *</Label>
        <Input id="farm_name" placeholder="e.g. Green Valley Farm" {...register('farm_name')} />
        {errors.farm_name && <p className="text-xs text-destructive">{errors.farm_name.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="owner_name">Owner *</Label>
        <Input id="owner_name" placeholder="Owner or managing entity" {...register('owner_name')} />
        {errors.owner_name && <p className="text-xs text-destructive">{errors.owner_name.message}</p>}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-2">
          <Label htmlFor="city">City *</Label>
          <Input id="city" {...register('city')} />
          {errors.city && <p className="text-xs text-destructive">{errors.city.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State *</Label>
          <Input id="state" {...register('state')} />
          {errors.state && <p className="text-xs text-destructive">{errors.state.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country *</Label>
          <Input id="country" {...register('country')} />
          {errors.country && <p className="text-xs text-destructive">{errors.country.message}</p>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="latitude">Latitude *</Label>
          <Input id="latitude" type="number" step="any" placeholder="-90 to 90" {...register('latitude')} />
          {errors.latitude && <p className="text-xs text-destructive">{errors.latitude.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="longitude">Longitude *</Label>
          <Input id="longitude" type="number" step="any" placeholder="-180 to 180" {...register('longitude')} />
          {errors.longitude && <p className="text-xs text-destructive">{errors.longitude.message}</p>}
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="total_area_hectares">Total Area (ha) *</Label>
        <Input id="total_area_hectares" type="number" step="0.01" {...register('total_area_hectares')} />
        {errors.total_area_hectares && (
          <p className="text-xs text-destructive">{errors.total_area_hectares.message}</p>
        )}
      </div>
      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : 'Create Farm'}
        </Button>
      </DialogFooter>
    </form>
  )
}

function FarmEditForm({
  defaultValues,
  onSubmit,
  isPending,
  onCancel,
}: {
  defaultValues: FarmEditFormValues
  onSubmit: (values: FarmEditFormValues) => void
  isPending: boolean
  onCancel: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FarmEditFormValues>({
    resolver: zodResolver(farmEditSchema),
    defaultValues,
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
      <div className="space-y-2">
        <Label htmlFor="farm_name">Farm Name *</Label>
        <Input id="farm_name" placeholder="e.g. Green Valley Farm" {...register('farm_name')} />
        {errors.farm_name && <p className="text-xs text-destructive">{errors.farm_name.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="owner_name">Owner *</Label>
        <Input id="owner_name" placeholder="Owner or managing entity" {...register('owner_name')} />
        {errors.owner_name && <p className="text-xs text-destructive">{errors.owner_name.message}</p>}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-2">
          <Label htmlFor="city">City *</Label>
          <Input id="city" {...register('city')} />
          {errors.city && <p className="text-xs text-destructive">{errors.city.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State *</Label>
          <Input id="state" {...register('state')} />
          {errors.state && <p className="text-xs text-destructive">{errors.state.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country *</Label>
          <Input id="country" {...register('country')} />
          {errors.country && <p className="text-xs text-destructive">{errors.country.message}</p>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="latitude">Latitude *</Label>
          <Input id="latitude" type="number" step="any" placeholder="-90 to 90" {...register('latitude')} />
          {errors.latitude && <p className="text-xs text-destructive">{errors.latitude.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="longitude">Longitude *</Label>
          <Input id="longitude" type="number" step="any" placeholder="-180 to 180" {...register('longitude')} />
          {errors.longitude && <p className="text-xs text-destructive">{errors.longitude.message}</p>}
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="total_area_hectares">Total Area (ha) *</Label>
        <Input id="total_area_hectares" type="number" step="0.01" {...register('total_area_hectares')} />
        {errors.total_area_hectares && (
          <p className="text-xs text-destructive">{errors.total_area_hectares.message}</p>
        )}
      </div>
      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  )
}

function farmToEditDefaults(farm: Farm): FarmEditFormValues {
  return {
    farm_name: farm.farm_name,
    owner_name: farm.owner_name,
    country: farm.country,
    state: farm.state,
    city: farm.city,
    latitude: String(decimalFromApi(farm.latitude) ?? ''),
    longitude: String(decimalFromApi(farm.longitude) ?? ''),
    total_area_hectares: String(decimalFromApi(farm.total_area_hectares) ?? ''),
  }
}

function DeleteConfirmDialog({
  farm,
  open,
  onClose,
}: {
  farm: Farm | null
  open: boolean
  onClose: () => void
}) {
  const { mutate: deleteFarm, isPending } = useDeleteFarm()

  function handleDelete() {
    if (!farm) return
    deleteFarm(farm.id, { onSuccess: onClose })
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Farm</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{farm ? farmDisplayName(farm) : ''}</strong>? This action cannot be
            undone and will remove all associated data.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={isPending}>
            {isPending ? 'Deleting…' : 'Delete Farm'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function Farms() {
  const { data: farms, isLoading, isError } = useFarms()
  const { mutate: createFarm, isPending: creating } = useCreateFarm()
  const { mutate: updateFarm, isPending: updating } = useUpdateFarm()

  const [createOpen, setCreateOpen] = useState(false)
  const [editFarm, setEditFarm] = useState<Farm | null>(null)
  const [deleteFarm, setDeleteFarm] = useState<Farm | null>(null)

  function handleCreate(values: FarmCreateFormValues) {
    createFarm(toCreatePayload(values), { onSuccess: () => setCreateOpen(false) })
  }

  function handleEdit(values: FarmEditFormValues) {
    if (!editFarm) return
    updateFarm(
      { id: editFarm.id, payload: toUpdatePayload(values) },
      { onSuccess: () => setEditFarm(null) },
    )
  }

  const totalArea = farms?.reduce((s, f) => s + (decimalFromApi(f.total_area_hectares) ?? 0), 0) ?? 0
  const activeCount = farms?.filter((f) => f.is_active).length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {farms ? `${farms.length} farm${farms.length !== 1 ? 's' : ''} registered` : ''}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Farm
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">{farms?.length ?? '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Farms</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {farms ? totalArea.toFixed(1) : '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Area (ha)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">{farms ? activeCount : '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Active</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">All Farms</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load farms. Is the backend running?
            </div>
          ) : farms?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Tractor className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No farms yet</p>
              <p className="text-sm">Click &quot;Add Farm&quot; to register your first farm.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Farm</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Area</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {farms?.map((farm) => (
                  <TableRow key={farm.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{farmDisplayName(farm)}</p>
                        <p className="text-xs text-muted-foreground">{farm.farm_code}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatFarmLocation(farm)}</TableCell>
                    <TableCell>
                      {decimalFromApi(farm.total_area_hectares) != null
                        ? `${decimalFromApi(farm.total_area_hectares)} ha`
                        : '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={farm.is_active ? 'success' : 'secondary'}>
                        {farm.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDate(farm.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditFarm(farm)}
                          className="h-8 w-8"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteFarm(farm)}
                          className="h-8 w-8 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Register New Farm</DialogTitle>
            <DialogDescription>Add a new agricultural farm to the platform.</DialogDescription>
          </DialogHeader>
          <FarmCreateForm onSubmit={handleCreate} isPending={creating} onCancel={() => setCreateOpen(false)} />
        </DialogContent>
      </Dialog>

      <Dialog open={!!editFarm} onOpenChange={(v) => !v && setEditFarm(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Farm</DialogTitle>
            <DialogDescription>
              Update details for {editFarm ? farmDisplayName(editFarm) : ''}.
            </DialogDescription>
          </DialogHeader>
          {editFarm && (
            <FarmEditForm
              defaultValues={farmToEditDefaults(editFarm)}
              onSubmit={handleEdit}
              isPending={updating}
              onCancel={() => setEditFarm(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      <DeleteConfirmDialog
        farm={deleteFarm}
        open={!!deleteFarm}
        onClose={() => setDeleteFarm(null)}
      />
    </div>
  )
}
