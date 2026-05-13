import { RealApiClient } from './realClient'
import type { ApiClient } from './client'

export const api: ApiClient = new RealApiClient()
export const API_MODE = 'real'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
export const IS_BACKEND_CONFIGURED = true

export type { ApiClient } from './client'
export { ApiErrorCode } from './errors'
export type { ApiError } from './errors'
