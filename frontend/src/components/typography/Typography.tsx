import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface TypographyProps {
  children: ReactNode
  className?: string
}

export function H1({ children, className }: TypographyProps) {
  return (
    <h1 className={cn('text-4xl font-bold text-slate-900 tracking-tight', className)}>
      {children}
    </h1>
  )
}

export function H2({ children, className }: TypographyProps) {
  return (
    <h2 className={cn('text-3xl font-bold text-slate-900 tracking-tight', className)}>
      {children}
    </h2>
  )
}

export function H3({ children, className }: TypographyProps) {
  return (
    <h3 className={cn('text-2xl font-semibold text-slate-900 tracking-tight', className)}>
      {children}
    </h3>
  )
}

export function H4({ children, className }: TypographyProps) {
  return (
    <h4 className={cn('text-xl font-semibold text-slate-900 tracking-tight', className)}>
      {children}
    </h4>
  )
}

export function SectionTitle({ children, className }: TypographyProps) {
  return (
    <h3 className={cn('text-lg font-semibold text-slate-900', className)}>
      {children}
    </h3>
  )
}

export function Subtitle({ children, className }: TypographyProps) {
  return (
    <p className={cn('text-base text-slate-600', className)}>
      {children}
    </p>
  )
}

export function Label({ children, className }: TypographyProps) {
  return (
    <span className={cn('text-xs font-medium text-slate-700', className)}>
      {children}
    </span>
  )
}

interface ProseProps {
  children: ReactNode
  className?: string
}

export function Prose({ children, className }: ProseProps) {
  return (
    <div className={cn('prose prose-slate max-w-none', className)}>
      {children}
    </div>
  )
}
