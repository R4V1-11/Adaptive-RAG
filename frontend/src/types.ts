export type Route = "rag" | "web" | "direct" | "rejected";

export interface DocSource {
  text: string;
  score: number;
  source?: string | null;
}

export interface WebSource {
  text: string;
  url: string;
}

export type Source = DocSource | WebSource;

export interface AskResponse {
  answer: string;
  sources: Source[];
  route: Route;
  fallback?: boolean;
}

export interface UploadResponse {
  filename: string;
  status: string;
  characters_extracted: number;
  chunks_stored: number;
}

export interface IndexedDocument {
  name: string;
  chunks: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  route?: Route;
  fallback?: boolean;
  sources?: Source[];
  scope?: string | null;
  latencyMs?: number;
  error?: boolean;
  pending?: boolean;
}

export type HealthStatus = "checking" | "online" | "offline";

export function isWebSource(s: Source): s is WebSource {
  return "url" in s;
}
