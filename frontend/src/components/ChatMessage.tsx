import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AlertCircle, Bot, User } from "lucide-react";
import type { Message } from "../types";
import RouteBadge from "./RouteBadge";
import SourceList from "./SourceList";

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-indigo-600 text-white" : "bg-white text-indigo-600 ring-1 ring-slate-200"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={`min-w-0 max-w-[85%] ${isUser ? "items-end" : ""} flex flex-col`}>
        {isUser ? (
          <div className="rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-2.5 text-sm text-white shadow-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
            {message.scope && (
              <p className="mt-1 text-[11px] text-indigo-200">in {message.scope}</p>
            )}
          </div>
        ) : (
          <div
            className={`rounded-2xl rounded-tl-sm px-4 py-3 text-sm shadow-sm ring-1 ${
              message.error ? "bg-rose-50 ring-rose-200" : "bg-white ring-slate-200"
            }`}
          >
            {message.pending ? (
              <div className="flex items-center gap-2 text-slate-500">
                <span className="flex gap-1">
                  <span className="dot h-1.5 w-1.5 rounded-full bg-slate-400" />
                  <span className="dot h-1.5 w-1.5 rounded-full bg-slate-400" />
                  <span className="dot h-1.5 w-1.5 rounded-full bg-slate-400" />
                </span>
                <span className="text-xs">Routing query, retrieving and grading context…</span>
              </div>
            ) : message.error ? (
              <p className="flex items-start gap-2 text-rose-700">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {message.content}
              </p>
            ) : (
              <>
                {message.route && (
                  <div className="mb-2 flex items-center gap-2">
                    <RouteBadge route={message.route} />
                    {message.latencyMs !== undefined && (
                      <span className="text-[11px] text-slate-400">
                        {(message.latencyMs / 1000).toFixed(1)}s
                      </span>
                    )}
                  </div>
                )}
                <div className="prose prose-sm prose-slate max-w-none prose-pre:bg-slate-900 prose-headings:mt-3 prose-p:my-1.5">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                </div>
                {message.sources && <SourceList sources={message.sources} />}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
