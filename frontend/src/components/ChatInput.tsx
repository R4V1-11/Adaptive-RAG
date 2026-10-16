import { useEffect, useRef, useState } from "react";
import { SendHorizonal } from "lucide-react";

const MAX_LENGTH = 500; // mirrors MAX_QUERY_LENGTH in backend/services/guardrails.py

interface Props {
  disabled: boolean;
  onSend: (query: string) => void;
  placeholder: string;
}

export default function ChatInput({ disabled, onSend, placeholder }: Props) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const tooLong = value.length > MAX_LENGTH;
  const canSend = !disabled && value.trim().length > 0 && !tooLong;

  function submit() {
    if (!canSend) return;
    onSend(value.trim());
    setValue("");
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100">
      <div className="flex items-end gap-2">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={placeholder}
          className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-slate-400"
        />
        <button
          onClick={submit}
          disabled={!canSend}
          aria-label="Send"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
        >
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>
      <div className="flex justify-between px-2 pt-1 text-[11px] text-slate-400">
        <span>Enter to send · Shift+Enter for new line</span>
        <span className={tooLong ? "font-medium text-rose-600" : ""}>
          {value.length}/{MAX_LENGTH}
        </span>
      </div>
    </div>
  );
}
