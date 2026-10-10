import { useMemo } from 'react'
import { Tractor, Layers, BellRing, Lightbulb, TrendingUp, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import { useAlertsForFieldIds } from '@/api/alerts'
import { useRecommendationsForFieldIds } from '@/api/recommendations'
import { formatDateTime } from '@/lib/utils'
import { decimalFromApi, formatFarmLocation, farmDisplayName } from '@/lib/farm'
import type { AlertSeverity } from '@/types'

const severityVariant: Record<AlertSeverity, 'critical' | 'destructive' | 'warning' | 'info'> = {
  CRITICAL: 'critical',
  HIGH: 'destructive',
  WARNING: 'warning',
  INFO: 'info',
}

function fieldIdStr(id: number | string): string {
  return String(id)
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
  loading,
}: {
  label: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  color: string
  sub?: string
  loading?: boolean
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            {loading ? (
              <Skeleton className="mt-2 h-8 w-16" />
            ) : (
              <p className="mt-1 text-3xl font-bold text-foreground">{value}</p>
            )}
            {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
          </div>
          <div className={`rounded-lg p-3 ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function Dashboard() {
  const { data: farms, isLoading: farmsLoading } = useFarms()
  const { data: allFields = [], isLoading: fieldsLoading } = useFields()
  const fieldIds = useMemo(() => allFields.map((f) => fieldIdStr(f.id)), [allFields])

  const { data: allAlerts = [], isLoading: alertsLoading } = useAlertsForFieldIds(fieldIds)
  const { data: recommendations = [], isLoading: recsLoading } = useRecommendationsForFieldIds(fieldIds)

  const totalFarms = farms?.length ?? 0
  const recentAlerts = allAlerts.slice(0, 5)
  const activeAlerts = allAlerts.filter((a) => !a.is_acknowledged).length
  const criticalCount = allAlerts.filter(
    (a) => a.severity === 'CRITICAL' && !a.is_acknowledged,
  ).length
  const pendingRecs = recommendations.filter(
    (r) => r.status === 'PENDING' || r.status === 'ACTIVE',
  ).length

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Farms"
          value={totalFarms}
          icon={Tractor}
          color="bg-green-600"
          sub="Registered agricultural units"
          loading={farmsLoading}
        />
        <StatCard
          label="Active Alerts"
          value={activeAlerts}
          icon={BellRing}
          color={criticalCount > 0 ? 'bg-red-500' : 'bg-amber-500'}
          sub={criticalCount > 0 ? `${criticalCount} critical` : 'No critical alerts'}
          loading={alertsLoading || fieldsLoading}
        />
        <StatCard
          label="Open Recommendations"
          value={pendingRecs}
          icon={Lightbulb}
          color="bg-blue-500"
          sub="Pending or active"
          loading={recsLoading || fieldsLoading}
        />
        <StatCard
          label="Fields Monitored"
          value={allFields.length}
          icon={Layers}
          color="bg-violet-500"
          sub="Across all farms"
          loading={fieldsLoading}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Alert Severity Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alertsLoading ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)
            ) : (
              (['CRITICAL', 'HIGH', 'WARNING', 'INFO'] as AlertSeverity[]).map((sev) => {
                const count = allAlerts.filter((a) => a.severity === sev && !a.is_acknowledged).length
                const total = activeAlerts || 1
                const pct = Math.round((count / total) * 100)
                const barColors: Record<AlertSeverity, string> = {
                  CRITICAL: 'bg-red-500',
                  HIGH: 'bg-orange-400',
                  WARNING: 'bg-amber-400',
                  INFO: 'bg-blue-400',
                }
                return (
                  <div key={sev}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium">{sev}</span>
                      <span className="text-muted-foreground">{count} active</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className={`h-2 rounded-full ${barColors[sev]} transition-all`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Recent Alerts</CardTitle>
              {criticalCount > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-red-600">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>{criticalCount} critical</span>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {alertsLoading ? (
              <div className="space-y-3 p-6">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : recentAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <TrendingUp className="mb-2 h-8 w-8 opacity-30" />
                <p className="text-sm">No alerts — all systems healthy</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Triggered</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-medium max-w-[140px] truncate">
                        {alert.title}
                      </TableCell>
                      <TableCell>
                        <Badge variant={severityVariant[alert.severity]}>
                          {alert.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-muted-foreground">
                        {alert.message}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {formatDateTime(alert.triggered_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Registered Farms</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {farmsLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : farms?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Tractor className="mb-2 h-8 w-8 opacity-30" />
              <p className="text-sm">No farms registered yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Farm Name</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Area (ha)</TableHead>
                  <TableHead>Registered</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {farms?.map((farm) => (
                  <TableRow key={farm.id}>
                    <TableCell className="font-medium">{farmDisplayName(farm)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatFarmLocation(farm)}</TableCell>
                    <TableCell>
                      {decimalFromApi(farm.total_area_hectares) != null
                        ? `${decimalFromApi(farm.total_area_hectares)} ha`
                        : '—'}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(farm.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
