import { create } from 'zustand'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  selectedFarmId: number | null
  setSelectedFarm: (id: number | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  selectedFarmId: null,
  setSelectedFarm: (id) => set({ selectedFarmId: id }),
}))
