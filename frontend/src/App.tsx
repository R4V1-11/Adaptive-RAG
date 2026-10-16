import { useCallback, useEffect, useRef, useState } from "react";
import { FileSearch, Globe, Menu, ShieldCheck, Sparkles, Trash2 } from "lucide-react";
import * as api from "./api";
import Sidebar from "./components/Sidebar";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import type { HealthStatus, IndexedDocument, Message } from "./types";

const uid = () => Math.random().toString(36).slice(2, 10);

const EXAMPLES = [
  { icon: FileSearch, text: "Summarize the key terms of the loan agreement" },
  { icon: Globe, text: "What is the latest news about Nvidia stock?" },
  { icon: Sparkles, text: "Explain the difference between RAG and fine-tuning" },
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<IndexedDocument[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus>("checking");
  const [busy, setBusy] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshDocuments = useCallback(async () => {
    const online = await api.checkHealth();
    setHealth(online ? "online" : "offline");
    if (!online) return;
    try {
      setDocuments(await api.listDocuments());
    } catch {
      /* keep previous list */
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(query: string) {
    const pendingId = uid();
    setMessages((m) => [
      ...m,
      { id: uid(), role: "user", content: query, scope: selected },
      { id: pendingId, role: "assistant", content: "", pending: true },
    ]);
    setBusy(true);

    const started = performance.now();
    let reply: Message;
    try {
      const res = await api.ask(query, selected);
      reply = {
        id: pendingId,
        role: "assistant",
        content: res.answer,
        route: res.route,
        fallback: res.fallback,
        sources: res.sources,
        latencyMs: performance.now() - started,
      };
    } catch (e) {
      reply = { id: pendingId, role: "assistant", content: (e as Error).message, error: true };
    }

    setMessages((m) => m.map((msg) => (msg.id === pendingId ? reply : msg)));
    setBusy(false);
  }

  function handleUploaded(name: string) {
    refreshDocuments();
    setSelected(name);
  }

  const sidebarProps = {
    documents,
    selected,
    onSelect: (name: string | null) => {
      setSelected(name);
      setSidebarOpen(false);
    },
    onUploaded: handleUploaded,
    onRefresh: refreshDocuments,
    health,
  };

  return (
    <div className="flex h-full">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <Sidebar {...sidebarProps} />
      </div>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setSidebarOpen(false)} />
          <div className="relative z-10 h-full">
            <Sidebar {...sidebarProps} onClose={() => setSidebarOpen(false)} />
          </div>
        </div>
      )}

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur lg:px-8">
          <button onClick={() => setSidebarOpen(true)} className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Open sidebar">
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-slate-400">Scope</p>
            <p className="truncate text-sm font-medium text-slate-800">
              {selected ?? "All sources — documents, web & general knowledge"}
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              disabled={busy}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-slate-500 hover:bg-slate-100 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </button>
          )}
        </header>

        <div className="scrollbar-thin flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 py-8 lg:px-8">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center pt-10 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-200">
                  <ShieldCheck className="h-7 w-7" />
                </div>
                <h2 className="mt-5 text-2xl font-semibold text-slate-900">Ask anything</h2>
                <p className="mt-2 max-w-md text-sm text-slate-500">
                  Each question is routed automatically: answered from your PDFs when retrieval is confident,
                  from live web search when it needs fresh data, or directly by the LLM otherwise.
                </p>
                <div className="mt-8 grid w-full gap-3 sm:grid-cols-3">
                  {EXAMPLES.map(({ icon: Icon, text }) => (
                    <button
                      key={text}
                      onClick={() => send(text)}
                      disabled={busy || health === "offline"}
                      className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm text-slate-600 shadow-sm transition hover:border-indigo-300 hover:shadow disabled:opacity-50"
                    >
                      <Icon className="mb-2 h-4 w-4 text-indigo-500" />
                      {text}
                    </button>
                  ))}
                </div>
                {health === "offline" && (
                  <p className="mt-6 rounded-lg bg-rose-50 px-4 py-2 text-xs text-rose-700 ring-1 ring-rose-200">
                    Backend unreachable. Start it with <code className="font-mono">uvicorn main:app --reload</code> in{" "}
                    <code className="font-mono">backend/</code>.
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((m) => (
                  <ChatMessage key={m.id} message={m} />
                ))}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-slate-200 bg-slate-50 px-4 py-4 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <ChatInput
              disabled={busy}
              onSend={send}
              placeholder={selected ? `Ask about ${selected}…` : "Ask a question…"}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
