import { useState } from 'react'
import { SettingsLayout } from '@/components/layout/SettingsLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle2 } from 'lucide-react'
import { useTheme } from '@/lib/hooks/use-theme'

export function Preferences() {
  const { theme, setTheme } = useTheme()
  const [density, setDensity] = useState<'comfortable' | 'compact'>('comfortable')
  const [tableRowSize, setTableRowSize] = useState(48)
  const [enableNotifications, setEnableNotifications] = useState(true)
  const [autoSaveDrafts, setAutoSaveDrafts] = useState(true)
  const [showLineNumbers, setShowLineNumbers] = useState(false)
  const [showToast, setShowToast] = useState(false)

  const handleSave = () => {
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  return (
    <SettingsLayout>
      <div className="space-y-6">
        {showToast && (
          <div className="fixed top-4 right-4 z-50 bg-primary text-primary-foreground px-4 py-3 rounded-md shadow-lg flex items-center gap-2 animate-in slide-in-from-top">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-sm font-medium">Preferences saved locally (mock)</span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Theme and display preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Theme</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={theme}
                onChange={(e) => setTheme(e.target.value as typeof theme)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
              <p className="text-xs text-muted-foreground">
                Choose your preferred color scheme
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Density</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setDensity('comfortable')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${density === 'comfortable'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                    }`}
                >
                  Comfortable
                </button>
                <button
                  type="button"
                  onClick={() => setDensity('compact')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${density === 'compact'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                    }`}
                >
                  Compact
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Adjust spacing and padding throughout the UI
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Table Settings</CardTitle>
            <CardDescription>Customize table display</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Row Height: {tableRowSize}px</label>
              <input
                type="range"
                min="32"
                max="64"
                step="4"
                value={tableRowSize}
                onChange={(e) => setTableRowSize(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Compact (32px)</span>
                <span>Comfortable (64px)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Editor</CardTitle>
            <CardDescription>Code and text editor preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium">Show Line Numbers</label>
                <p className="text-xs text-muted-foreground">Display line numbers in code editors</p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={showLineNumbers}
                onClick={() => setShowLineNumbers(!showLineNumbers)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${showLineNumbers ? 'bg-primary' : 'bg-input'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${showLineNumbers ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Configure notification preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium">Enable Notifications</label>
                <p className="text-xs text-muted-foreground">Show notifications for run completion and errors</p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={enableNotifications}
                onClick={() => setEnableNotifications(!enableNotifications)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enableNotifications ? 'bg-primary' : 'bg-input'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${enableNotifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium">Auto-save Drafts</label>
                <p className="text-xs text-muted-foreground">Automatically save paper drafts every 30 seconds</p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={autoSaveDrafts}
                onClick={() => setAutoSaveDrafts(!autoSaveDrafts)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${autoSaveDrafts ? 'bg-primary' : 'bg-input'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${autoSaveDrafts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleSave}>Save Preferences</Button>
        </div>
      </div>
    </SettingsLayout>
  )
}
