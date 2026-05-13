/**
 * Code Projects API Client
 * 
 * Typed API client for code project browsing, search, export, VSCode link.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Types

export interface CodeProjectV2 {
  id: string;
  title: string;
  description?: string;
  language?: string;
  framework?: string;
  license?: string;
  sourceIdeaSessionId?: string;
  sourceCandidateId?: string;
  rootStoragePath?: string;
  repoSchemaVersion: number;
  fileCount: number;
  totalSizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectListResponse {
  projects: CodeProjectV2[];
  total: number;
}

export interface TreeEntry {
  name: string;
  path: string;
  isDir: boolean;
  size: number;
}

export interface TreeResponse {
  projectId: string;
  path: string;
  entries: TreeEntry[];
}

export interface FileContentResponse {
  projectId: string;
  path: string;
  content: string;
  size: number;
  language?: string;
}

export interface SearchResult {
  path: string;
  line?: number;
  content?: string;
  isDir?: boolean;
}

export interface SearchResponse {
  projectId: string;
  query: string;
  mode: string;
  results: SearchResult[];
  total: number;
}

export interface ExportResponse {
  id: string;
  projectId: string;
  kind: string;
  size: number;
  sha256?: string;
  createdAt: string;
}

export interface VSCodeLinkResponse {
  uri: string;
  path: string;
  exists: boolean;
  instructions: string;
}

export interface CreateProjectRequest {
  title: string;
  description?: string;
  language?: string;
  framework?: string;
  license?: string;
  sourceIdeaSessionId?: string;
  sourceCandidateId?: string;
  files?: Array<{ path: string; content: string }>;
}

// Helper

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// API Functions

export async function createProject(request: CreateProjectRequest): Promise<CodeProjectV2> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
}

export async function listProjects(params?: {
  search?: string;
  language?: string;
  limit?: number;
  offset?: number;
}): Promise<ProjectListResponse> {
  const sp = new URLSearchParams();
  if (params?.search) sp.set('search', params.search);
  if (params?.language) sp.set('language', params.language);
  if (params?.limit) sp.set('limit', params.limit.toString());
  if (params?.offset) sp.set('offset', params.offset.toString());
  const qs = sp.toString() ? `?${sp}` : '';
  return fetchJSON(`${API_BASE}/api/v1/code/projects${qs}`);
}

export async function getProject(projectId: string): Promise<CodeProjectV2> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}`);
}

export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/code/projects/${projectId}`, { method: 'DELETE' });
  if (!response.ok && response.status !== 204) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

export async function getTree(projectId: string, path: string = ''): Promise<TreeResponse> {
  const sp = new URLSearchParams();
  if (path) sp.set('path', path);
  const qs = sp.toString() ? `?${sp}` : '';
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}/tree${qs}`);
}

export async function getFileContent(projectId: string, path: string): Promise<FileContentResponse> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}/file?path=${encodeURIComponent(path)}`);
}

export function getFileDownloadUrl(projectId: string, path: string): string {
  return `${API_BASE}/api/v1/code/projects/${projectId}/file/download?path=${encodeURIComponent(path)}`;
}

export async function searchProject(projectId: string, query: string, mode: 'path' | 'content' = 'path'): Promise<SearchResponse> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}/search?q=${encodeURIComponent(query)}&mode=${mode}`);
}

export async function exportProject(projectId: string): Promise<ExportResponse> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}/export`, { method: 'POST' });
}

export function getExportDownloadUrl(exportId: string): string {
  return `${API_BASE}/api/v1/code/projects/exports/${exportId}/download`;
}

export async function getVSCodeLink(projectId: string): Promise<VSCodeLinkResponse> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/${projectId}/vscode-link`);
}

export async function generateSampleProject(title: string, language: string = 'python', description?: string): Promise<CodeProjectV2> {
  return fetchJSON(`${API_BASE}/api/v1/code/projects/generate-sample`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, language, description }),
  });
}
