import { Outlet, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Github, FileText, Activity } from 'lucide-react'
import { AppLogo } from '@/components/branding/AppLogo'

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-[#F6F7F9]">
      {/* Top Navigation */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="hover:opacity-80 transition-opacity">
              <AppLogo size="md" variant="full" />
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-8">
              <a
                href="#"
                className="text-sm text-slate-600 hover:text-teal-600 transition-colors flex items-center gap-1"
                aria-label="Documentation"
              >
                <FileText className="h-4 w-4" />
                Docs
              </a>
              <a
                href="#"
                className="text-sm text-slate-600 hover:text-teal-600 transition-colors flex items-center gap-1"
                aria-label="System Status"
              >
                <Activity className="h-4 w-4" />
                Status
              </a>
              <a
                href="#"
                className="text-sm text-slate-600 hover:text-teal-600 transition-colors flex items-center gap-1"
                aria-label="GitHub Repository"
              >
                <Github className="h-4 w-4" />
                GitHub
              </a>
            </nav>

            {/* CTA Button */}
            <Link to="/research/planning">
              <Button className="bg-teal-600 hover:bg-teal-700 shadow-sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <main>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-24">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1">
              <div className="flex items-center gap-2 font-semibold text-slate-900 mb-4">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">LS</span>
                </div>
                <span>FAROS</span>
              </div>
              <p className="text-sm text-slate-600">
                Automate AI research workflows with intelligent orchestration.
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-slate-900 mb-3">Platform</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><Link to="/research/planning" className="hover:text-teal-600">Research</Link></li>
                <li><Link to="/runs" className="hover:text-teal-600">Runs</Link></li>
                <li><Link to="/experiments" className="hover:text-teal-600">Experiments</Link></li>
                <li><Link to="/papers" className="hover:text-teal-600">Papers</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-slate-900 mb-3">Resources</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><a href="#" className="hover:text-teal-600">Documentation</a></li>
                <li><a href="#" className="hover:text-teal-600">API Reference</a></li>
                <li><a href="#" className="hover:text-teal-600">Examples</a></li>
                <li><a href="#" className="hover:text-teal-600">Changelog</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-slate-900 mb-3">Community</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><a href="#" className="hover:text-teal-600">GitHub</a></li>
                <li><a href="#" className="hover:text-teal-600">Discord</a></li>
                <li><a href="#" className="hover:text-teal-600">Twitter</a></li>
                <li><a href="#" className="hover:text-teal-600">Blog</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-200 mt-8 pt-8 text-center text-sm text-slate-600">
            © 2026 FAROS. A foundation AutoResearch runtime for extensible research workflows.
          </div>
        </div>
      </footer>
    </div>
  )
}
