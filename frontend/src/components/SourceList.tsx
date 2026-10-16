import { useState } from "react";
import { ChevronDown, ExternalLink, FileText } from "lucide-react";
import { isWebSource, type Source } from "../types";

function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export default function SourceList({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;

  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700"
      >
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {sources.length} source{sources.length > 1 ? "s" : ""}
      </button>

      {open && (
        <ul className="mt-2 space-y-2">
          {sources.map((s, i) => (
            <li key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
              <div className="mb-1 flex items-center justify-between gap-2">
                {isWebSource(s) ? (
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 truncate font-medium text-sky-700 hover:underline"
                  >
                    <ExternalLink className="h-3 w-3 shrink-0" />
                    {hostname(s.url)}
                  </a>
                ) : (
                  <>
                    <span className="inline-flex items-center gap-1 truncate font-medium text-slate-700">
                      <FileText className="h-3 w-3 shrink-0" />
                      {s.source ?? "Document"}
                    </span>
                    <span
                      className="shrink-0 rounded bg-emerald-100 px-1.5 py-0.5 font-mono text-[10px] text-emerald-800"
                      title="Cosine similarity"
                    >
                      {s.score.toFixed(3)}
                    </span>
                  </>
                )}
              </div>
              <p className="line-clamp-4 whitespace-pre-line text-slate-600">{s.text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
