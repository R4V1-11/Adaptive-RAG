import { useRef, useState } from "react";
import { CheckCircle2, Loader2, UploadCloud, XCircle } from "lucide-react";
import { uploadPdf } from "../api";
import type { UploadResponse } from "../types";

const MAX_MB = 5; // mirrors MAX_FILE_SIZE_MB in backend/config.py

type Status =
  | { kind: "idle" }
  | { kind: "uploading"; name: string }
  | { kind: "done"; result: UploadResponse }
  | { kind: "error"; message: string };

export default function UploadZone({ onUploaded }: { onUploaded: (name: string) => void }) {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handle(file: File | undefined) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatus({ kind: "error", message: "Only PDF files are supported." });
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setStatus({ kind: "error", message: `File exceeds the ${MAX_MB} MB limit.` });
      return;
    }

    setStatus({ kind: "uploading", name: file.name });
    try {
      const result = await uploadPdf(file);
      setStatus({ kind: "done", result });
      onUploaded(result.filename);
    } catch (e) {
      setStatus({ kind: "error", message: (e as Error).message });
    }
  }

  const uploading = status.kind === "uploading";

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !uploading && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!uploading) handle(e.dataTransfer.files[0]);
        }}
        className={`flex cursor-pointer flex-col items-center gap-1.5 rounded-xl border-2 border-dashed px-4 py-5 text-center transition ${
          dragging
            ? "border-indigo-400 bg-indigo-50"
            : "border-slate-300 bg-white hover:border-indigo-300 hover:bg-slate-50"
        } ${uploading ? "pointer-events-none opacity-70" : ""}`}
      >
        {uploading ? (
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
        ) : (
          <UploadCloud className="h-6 w-6 text-indigo-500" />
        )}
        <p className="text-sm font-medium text-slate-700">
          {uploading ? "Indexing…" : "Drop a PDF or click to upload"}
        </p>
        <p className="text-xs text-slate-400">Max {MAX_MB} MB · extracted, chunked & embedded</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            handle(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      {status.kind === "uploading" && (
        <p className="mt-2 truncate text-xs text-slate-500">Processing {status.name}</p>
      )}
      {status.kind === "done" && (
        <p className="mt-2 flex items-start gap-1.5 text-xs text-emerald-700">
          <CheckCircle2 className="mt-px h-3.5 w-3.5 shrink-0" />
          <span className="min-w-0">
            <span className="block truncate font-medium">{status.result.filename}</span>
            {status.result.characters_extracted.toLocaleString()} chars → {status.result.chunks_stored} chunks
          </span>
        </p>
      )}
      {status.kind === "error" && (
        <p className="mt-2 flex items-start gap-1.5 text-xs text-rose-600">
          <XCircle className="mt-px h-3.5 w-3.5 shrink-0" />
          {status.message}
        </p>
      )}
    </div>
  );
}
