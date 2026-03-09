"use client";

import { CheckCircle, XCircle, AlertCircle } from "lucide-react";

interface Suggestion {
  field_name: string;
  old_value: any;
  suggested_value: any;
  reasoning: string;
}

interface Props {
  suggestions: Suggestion[];
  summary: string;
  onAccept: (suggestion: Suggestion) => void;
  onAcceptAll: () => void;
}

export function AISuggestionsPanel({ suggestions, summary, onAccept, onAcceptAll }: Props) {
  if (!suggestions?.length) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-blue-900">AI Suggested Corrections</h3>
        <button
          onClick={onAcceptAll}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
        >
          Accept All ({suggestions.length})
        </button>
      </div>

      {summary && <p className="text-sm text-blue-700">{summary}</p>}

      <div className="space-y-3">
        {suggestions.map((sug, i) => (
          <div key={i} className="bg-white border border-blue-200 rounded-lg p-4 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium text-gray-900 mb-2">
                  {sug.field_name.replace(/_/g, " ").toUpperCase()}
                </div>
                <div className="text-sm space-y-1 mb-2">
                  <div className="flex gap-2">
                    <span className="text-gray-500">Current:</span>
                    <code className="text-red-600 line-through">
                      {sug.old_value ?? "—"}
                    </code>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-gray-500">Suggested:</span>
                    <code className="text-green-700 font-semibold">
                      {sug.suggested_value}
                    </code>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{sug.reasoning}</p>
              </div>
              <button
                onClick={() => onAccept(sug)}
                className="ml-4 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors flex items-center gap-1"
              >
                <CheckCircle className="w-4 h-4" />
                Accept
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
