import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BellRing, LogOut, Settings, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFields } from '@/api/fields'
import { useAlertsForFieldIds } from '@/api/alerts'
import { useCurrentUser, useLogout } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { LoginDialog } from '@/components/auth/LoginDialog'

interface HeaderProps {
  title: string
  description?: string
}

export function Header({ title, description }: HeaderProps) {
  const navigate = useNavigate()
  const [loginOpen, setLoginOpen] = useState(false)
  const accessToken = useAuthStore((s) => s.accessToken)
  const storedUser = useAuthStore((s) => s.user)
  const logout = useLogout()
  const me = useCurrentUser(Boolean(accessToken))

  const displayEmail = me.data?.email ?? storedUser?.email

  const { data: fields = [] } = useFields()
  const fieldIds = useMemo(() => fields.map((f) => String(f.id)), [fields])
  const { data: alerts = [] } = useAlertsForFieldIds(fieldIds)
  const unacknowledgedCount = alerts.filter((a) => !a.is_acknowledged).length

  return (
    <>
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
          {accessToken ? (
            <div className="flex items-center gap-2">
              <span className="hidden max-w-[140px] truncate text-xs text-muted-foreground sm:inline">
                {displayEmail}
              </span>
              <Button variant="ghost" size="icon" aria-label="Sign out" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setLoginOpen(true)}>
              <User className="mr-2 h-4 w-4" />
              Sign in
            </Button>
          )}
        </div>
      </header>
      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </>
  )
}
