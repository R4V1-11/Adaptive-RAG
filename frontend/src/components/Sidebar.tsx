import { FileText, Layers, RefreshCw, Workflow, X } from "lucide-react";
import type { HealthStatus, IndexedDocument } from "../types";
import UploadZone from "./UploadZone";

interface Props {
  documents: IndexedDocument[];
  selected: string | null;
  onSelect: (name: string | null) => void;
  onUploaded: (name: string) => void;
  onRefresh: () => void;
  health: HealthStatus;
  onClose?: () => void;
}

const HEALTH = {
  checking: { dot: "bg-amber-400", label: "Connecting…" },
  online: { dot: "bg-emerald-500", label: "Backend online" },
  offline: { dot: "bg-rose-500", label: "Backend offline" },
};

export default function Sidebar({ documents, selected, onSelect, onUploaded, onRefresh, health, onClose }: Props) {
  const item = (active: boolean) =>
    `flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition ${
      active ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <aside className="flex h-full w-80 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
            <Workflow className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold leading-tight text-slate-900">Adaptive RAG</h1>
            <p className="text-xs text-slate-500">Agentic document Q&amp;A</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden" aria-label="Close sidebar">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <div className="px-5 pt-5">
        <UploadZone onUploaded={onUploaded} />
      </div>

      <div className="mt-6 flex items-center justify-between px-5">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Knowledge base</h2>
        <button onClick={onRefresh} className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600" aria-label="Refresh documents">
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      <nav className="scrollbar-thin mt-2 flex-1 space-y-0.5 overflow-y-auto px-3 pb-4">
        <button className={item(selected === null)} onClick={() => onSelect(null)}>
          <Layers className="h-4 w-4 shrink-0" />
          <span className="flex-1">All sources</span>
          <span className="text-[11px] text-slate-400">auto-route</span>
        </button>

        {documents.map((d) => (
          <button key={d.name} className={item(selected === d.name)} onClick={() => onSelect(d.name)} title={d.name}>
            <FileText className="h-4 w-4 shrink-0" />
            <span className="flex-1 truncate">{d.name}</span>
            <span className="shrink-0 text-[11px] text-slate-400">{d.chunks} chunks</span>
          </button>
        ))}

        {documents.length === 0 && health === "online" && (
          <p className="px-3 py-2 text-xs text-slate-400">No documents indexed yet.</p>
        )}
      </nav>

      <div className="flex items-center gap-2 border-t border-slate-200 px-5 py-3 text-xs text-slate-500">
        <span className={`h-2 w-2 rounded-full ${HEALTH[health].dot}`} />
        {HEALTH[health].label}
      </div>
    </aside>
  );
}
