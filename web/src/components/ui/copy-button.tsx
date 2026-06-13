"use client";

import { useState, useCallback } from "react";

interface CopyButtonProps {
  text: string;
  label?: string;
  className?: string;
}

export function CopyButton({ text, label = "复制", className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={`text-xs px-2 py-1 rounded transition-colors duration-150 cursor-pointer ${
        copied
          ? "bg-success/10 text-success"
          : "bg-bg-muted text-muted hover:bg-border hover:text-foreground"
      } ${className ?? ""}`}
    >
      {copied ? "已复制" : label}
    </button>
  );
}
