import { FileSearch, Globe, ShieldAlert, Sparkles } from "lucide-react";
import type { Route } from "../types";

const ROUTES: Record<Route, { label: string; className: string; Icon: typeof Globe; hint: string }> = {
  rag: {
    label: "Document RAG",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    Icon: FileSearch,
    hint: "Answered from your uploaded PDFs via vector search + LLM relevance grading",
  },
  web: {
    label: "Web Search",
    className: "bg-sky-50 text-sky-700 ring-sky-200",
    Icon: Globe,
    hint: "Query needed live information, so it was answered from Tavily web search",
  },
  direct: {
    label: "General Knowledge",
    className: "bg-violet-50 text-violet-700 ring-violet-200",
    Icon: Sparkles,
    hint: "Answered directly by the LLM from general knowledge",
  },
  rejected: {
    label: "Rejected by guardrails",
    className: "bg-rose-50 text-rose-700 ring-rose-200",
    Icon: ShieldAlert,
    hint: "The query failed input validation",
  },
};

export default function RouteBadge({ route }: { route: Route }) {
  const { label, className, Icon, hint } = ROUTES[route] ?? ROUTES.direct;
  return (
    <span
      title={hint}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${className}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}
