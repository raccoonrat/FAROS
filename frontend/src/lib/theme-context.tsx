import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export type ThemeId = 'default' | 'modern-academic' | 'professional-dark' | 'research-lab'

export interface ThemeOption {
  id: ThemeId
  name: string
  description: string
  preview: { bg: string; fg: string; accent: string; card: string }
}

export const THEMES: ThemeOption[] = [
  {
    id: 'default',
    name: 'System Default',
    description: 'Original light/dark mode based on system preference',
    preview: { bg: '#ffffff', fg: '#1a1a1a', accent: '#0066cc', card: '#ffffff' },
  },
  {
    id: 'modern-academic',
    name: 'Modern Academic',
    description: 'Neutral white + soft blue palette with thin sans fonts',
    preview: { bg: '#f5f7fa', fg: '#1e2a3a', accent: '#2d7dd2', card: '#ffffff' },
  },
  {
    id: 'professional-dark',
    name: 'Professional Dark',
    description: 'Dark background (#1E1E2E) with teal accents for code and papers',
    preview: { bg: '#1e1e2e', fg: '#c9d1e8', accent: '#20b2aa', card: '#282840' },
  },
  {
    id: 'research-lab',
    name: 'Research Lab',
    description: 'High contrast with serif headings, emphasis on figures',
    preview: { bg: '#f8f5f0', fg: '#2b1f1a', accent: '#0e8585', card: '#ffffff' },
  },
]

interface ThemeContextValue {
  theme: ThemeId
  setTheme: (t: ThemeId) => void
  themes: ThemeOption[]
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'default',
  setTheme: () => {},
  themes: THEMES,
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>(() => {
    const stored = localStorage.getItem('app-theme') as ThemeId | null
    return stored && THEMES.some(t => t.id === stored) ? stored : 'default'
  })

  const setTheme = (t: ThemeId) => {
    setThemeState(t)
    localStorage.setItem('app-theme', t)
  }

  useEffect(() => {
    const root = document.documentElement
    // Remove all theme classes
    root.classList.remove('theme-modern-academic', 'theme-professional-dark', 'theme-research-lab', 'dark')

    switch (theme) {
      case 'modern-academic':
        root.classList.add('theme-modern-academic')
        break
      case 'professional-dark':
        root.classList.add('theme-professional-dark')
        break
      case 'research-lab':
        root.classList.add('theme-research-lab')
        break
      default:
        // default: respect system preference
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
          root.classList.add('dark')
        }
        break
    }
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
