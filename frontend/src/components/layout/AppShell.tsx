import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { BackgroundLayer } from './BackgroundLayer'

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#F6F7F9]">
      <BackgroundLayer />
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
