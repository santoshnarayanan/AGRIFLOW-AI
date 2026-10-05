import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Tractor, Layers, Wheat, CloudSun,
  Activity, Droplets, BarChart3, Bug, Satellite, FlaskConical,
  BellRing, Lightbulb, ChevronLeft, Leaf,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/appStore'
import { Button } from '@/components/ui/button'

const navGroups = [
  {
    label: 'Overview',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    ],
  },
  {
    label: 'Farm Management',
    items: [
      { to: '/farms', icon: Tractor, label: 'Farms' },
      { to: '/fields', icon: Layers, label: 'Fields' },
      { to: '/crops', icon: Wheat, label: 'Crops' },
    ],
  },
  {
    label: 'Environmental',
    items: [
      { to: '/soil-profiles', icon: FlaskConical, label: 'Soil Profiles' },
      { to: '/weather', icon: CloudSun, label: 'Weather' },
      { to: '/sensors', icon: Activity, label: 'Sensors' },
    ],
  },
  {
    label: 'Operations',
    items: [
      { to: '/irrigation', icon: Droplets, label: 'Irrigation' },
      { to: '/yield', icon: BarChart3, label: 'Yield' },
      { to: '/disease', icon: Bug, label: 'Disease' },
      { to: '/satellite', icon: Satellite, label: 'Satellite' },
    ],
  },
  {
    label: 'AI Intelligence',
    items: [
      { to: '/recommendations', icon: Lightbulb, label: 'Recommendations' },
      { to: '/alerts', icon: BellRing, label: 'Alerts' },
    ],
  },
]

interface NavItemProps {
  to: string
  icon: React.ComponentType<{ className?: string }>
  label: string
  exact?: boolean
  collapsed: boolean
}

function NavItem({ to, icon: Icon, label, exact, collapsed }: NavItemProps) {
  const location = useLocation()
  const isActive = exact ? location.pathname === to : location.pathname.startsWith(to)

  return (
    <NavLink
      to={to}
      title={collapsed ? label : undefined}
      className={cn(
        'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'text-sidebar-foreground/70 hover:bg-white/10 hover:text-sidebar-foreground',
        collapsed && 'justify-center px-2'
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  )
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore()

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className={cn('flex h-16 items-center border-b border-sidebar-border px-4', sidebarCollapsed && 'justify-center px-2')}>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-sidebar-accent">
            <Leaf className="h-4 w-4 text-sidebar-accent-foreground" />
          </div>
          {!sidebarCollapsed && (
            <div>
              <p className="text-sm font-bold text-sidebar-foreground leading-tight">AGRIFLOW</p>
              <p className="text-[10px] text-sidebar-foreground/50 leading-tight">AI Platform</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        {navGroups.map((group) => (
          <div key={group.label}>
            {!sidebarCollapsed && (
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/40">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavItem key={item.to} {...item} collapsed={sidebarCollapsed} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-sidebar-border p-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="w-full text-sidebar-foreground/70 hover:bg-white/10 hover:text-sidebar-foreground"
        >
          <ChevronLeft className={cn('h-4 w-4 transition-transform', sidebarCollapsed && 'rotate-180')} />
        </Button>
      </div>
    </aside>
  )
}
