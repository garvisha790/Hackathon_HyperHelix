"use client";
import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { Send, Bot, User, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  has_data?: boolean;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI financial assistant. Ask me anything about your invoices, expenses, GST, or financial data. For example:\n\n- \"How much GST do I owe this month?\"\n- \"What are my top expenses?\"\n- \"Show invoices from Reliance\"\n- \"What's my total revenue?\"",
    },
  ]);
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askMutation = useMutation({
    mutationFn: (question: string) => api.post("/copilot/ask", { question }).then((r) => r.data),
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, intent: data.intent, has_data: data.has_data }]);
    },
    onError: () => {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I couldn't process that request. Please try again." }]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || askMutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    askMutation.mutate(input);
    setInput("");
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">AI Copilot</h1>
        <p className="mt-1 text-sm text-gray-500">Ask questions about your financial data in plain English</p>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border bg-white p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${msg.role === "user" ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600"}`}>
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${msg.role === "user" ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-800"}`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.intent && (
                <p className={`mt-2 text-xs ${msg.role === "user" ? "text-brand-200" : "text-gray-400"}`}>
                  Query type: {msg.intent}
                </p>
              )}
            </div>
          </div>
        ))}
        {askMutation.isPending && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
              <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
            </div>
            <div className="rounded-2xl bg-gray-100 px-4 py-3 text-sm text-gray-500">Thinking...</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about your finances..."
          className="flex-1 rounded-xl border px-4 py-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />
        <button
          onClick={handleSend}
          disabled={askMutation.isPending || !input.trim()}
          className="rounded-xl bg-brand-600 px-5 py-3 text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
