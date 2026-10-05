import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

const pageMeta: Record<string, { title: string; description: string }> = {
  '/': { title: 'Dashboard', description: 'Platform overview and key metrics' },
  '/farms': { title: 'Farms', description: 'Manage your agricultural farms' },
  '/fields': { title: 'Fields', description: 'Manage fields within your farms' },
  '/crops': { title: 'Crops', description: 'Track crop lifecycle and status' },
  '/soil-profiles': { title: 'Soil Profiles', description: 'Soil intelligence and analysis' },
  '/weather': { title: 'Weather', description: 'Weather observations and forecasts' },
  '/sensors': { title: 'Sensors', description: 'IoT sensor telemetry data' },
  '/irrigation': { title: 'Irrigation', description: 'Irrigation event management' },
  '/yield': { title: 'Yield', description: 'Harvest records and yield analytics' },
  '/disease': { title: 'Disease Observations', description: 'Disease detection and tracking' },
  '/satellite': { title: 'Satellite', description: 'NDVI, EVI and satellite indices' },
  '/recommendations': { title: 'Recommendations', description: 'AI-generated agronomic recommendations' },
  '/alerts': { title: 'Alerts', description: 'System and agronomic alerts' },
}

export function AppLayout() {
  const location = useLocation()
  const meta = pageMeta[location.pathname] ?? { title: 'AGRIFLOW-AI', description: '' }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title={meta.title} description={meta.description} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
