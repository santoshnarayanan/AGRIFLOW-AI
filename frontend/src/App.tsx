import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { Farms } from '@/pages/Farms'
import { Fields } from '@/pages/Fields'
import { Crops } from '@/pages/Crops'
import { SoilProfiles } from '@/pages/SoilProfiles'
import { Weather } from '@/pages/Weather'
import { Sensors } from '@/pages/Sensors'
import { Irrigation } from '@/pages/Irrigation'
import { Yield } from '@/pages/Yield'
import { Disease } from '@/pages/Disease'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-muted">
      <p className="text-muted-foreground">{label} — coming in next sprint</p>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="farms" element={<Farms />} />
            <Route path="fields" element={<Fields />} />
            <Route path="crops" element={<Crops />} />
            <Route path="soil-profiles" element={<SoilProfiles />} />
            <Route path="weather" element={<Weather />} />
            <Route path="sensors" element={<Sensors />} />
            <Route path="irrigation" element={<Irrigation />} />
            <Route path="yield" element={<Yield />} />
            <Route path="disease" element={<Disease />} />
            <Route path="satellite" element={<ComingSoon label="Satellite" />} />
            <Route path="recommendations" element={<ComingSoon label="Recommendations" />} />
            <Route path="alerts" element={<ComingSoon label="Alerts" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
