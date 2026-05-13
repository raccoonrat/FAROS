import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Settings, Sliders, Palette } from 'lucide-react'

interface SettingsLayoutProps {
  children: ReactNode
}

const settingsNav = [
  { path: '/settings/providers', label: 'LLM Providers', icon: Sliders },
  { path: '/settings/preferences', label: 'Preferences', icon: Palette },
]

export function SettingsLayout({ children }: SettingsLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-[#F6F7F9]">
      <div className="max-w-[1680px] w-full mx-auto px-4 sm:px-6 lg:px-10 2xl:max-w-[1840px] py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Settings className="h-8 w-8 text-teal-600" />
            <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
          </div>
          <p className="text-lg text-slate-600">Manage your workspace configuration and preferences</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Settings Navigation */}
          <nav className="lg:col-span-1" data-testid="settings-nav">
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-2 sticky top-6">
              <div className="space-y-1">
                {settingsNav.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200
                        ${isActive
                          ? 'bg-teal-50 text-teal-900 font-semibold border-l-4 border-teal-600'
                          : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                        }
                      `}
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-teal-600' : 'text-slate-500'}`} />
                      <span className="text-sm">{item.label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          </nav>

          {/* Right: Settings Panel */}
          <div className="lg:col-span-3" data-testid="settings-panel">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
