import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { BellRing, Settings, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFields } from '@/api/fields'
import { useAlertsForFieldIds } from '@/api/alerts'

interface HeaderProps {
  title: string
  description?: string
}

export function Header({ title, description }: HeaderProps) {
  const navigate = useNavigate()
  const { data: fields = [] } = useFields()
  const fieldIds = useMemo(() => fields.map((f) => String(f.id)), [fields])
  const { data: alerts = [] } = useAlertsForFieldIds(fieldIds)
  const unacknowledgedCount = alerts.filter((a) => !a.is_acknowledged).length

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={
            unacknowledgedCount > 0
              ? `${unacknowledgedCount} unacknowledged alerts`
              : 'Alerts'
          }
          onClick={() => navigate('/alerts')}
        >
          <BellRing className="h-4 w-4" />
          {unacknowledgedCount > 0 && (
            <span
              className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground"
            >
              {unacknowledgedCount > 99 ? '99+' : unacknowledgedCount}
            </span>
          )}
        </Button>
        <Button variant="ghost" size="icon" aria-label="Settings">
          <Settings className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Account">
          <User className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
