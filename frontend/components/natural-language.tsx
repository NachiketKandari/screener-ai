"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2 } from "lucide-react";

interface Props {
  onSubmit: (query: string) => void;
  loading: boolean;
}

export function NaturalLanguageInput({ onSubmit, loading }: Props) {
  const [query, setQuery] = useState("");

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <input
          type="text"
          placeholder='Try: "banks with PE under 15 and ROE above 20"'
          className="w-full border rounded-lg px-4 py-2.5 text-sm bg-background pr-10"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && query.trim()) {
              onSubmit(query.trim());
            }
          }}
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>
      <Button
        onClick={() => query.trim() && onSubmit(query.trim())}
        disabled={!query.trim() || loading}
        className="gap-1.5"
      >
        <Sparkles className="h-4 w-4" />
        Ask AI
      </Button>
    </div>
  );
}
