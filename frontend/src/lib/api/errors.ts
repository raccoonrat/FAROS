// API Error Handling
// Provides typed error codes and standardized error structure

export enum ApiErrorCode {
  UNAVAILABLE = 'UNAVAILABLE',
  UNAUTHORIZED = 'UNAUTHORIZED',
  NOT_IMPLEMENTED = 'NOT_IMPLEMENTED',
  BAD_REQUEST = 'BAD_REQUEST',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN',
}

export interface ApiError {
  code: ApiErrorCode
  message: string
  requestId?: string
  details?: Record<string, unknown>
}

export function toApiError(e: unknown, requestId?: string): ApiError {
  if (isApiError(e)) {
    return e
  }

  if (e instanceof Error) {
    // Map common error types
    if (e.name === 'AbortError' || e.message.includes('timeout')) {
      return {
        code: ApiErrorCode.TIMEOUT,
        message: e.message || 'Request timed out',
        requestId,
      }
    }

    if (e.message.includes('fetch') || e.message.includes('network')) {
      return {
        code: ApiErrorCode.UNAVAILABLE,
        message: 'Network error: Unable to reach backend',
        requestId,
      }
    }

    return {
      code: ApiErrorCode.UNKNOWN,
      message: e.message || 'An unknown error occurred',
      requestId,
    }
  }

  return {
    code: ApiErrorCode.UNKNOWN,
    message: String(e),
    requestId,
  }
}

export function isApiError(e: unknown): e is ApiError {
  return (
    typeof e === 'object' &&
    e !== null &&
    'code' in e &&
    'message' in e &&
    Object.values(ApiErrorCode).includes((e as ApiError).code)
  )
}

export function createApiError(
  code: ApiErrorCode,
  message: string,
  requestId?: string,
  details?: Record<string, unknown>
): ApiError {
  return { code, message, requestId, details }
}
