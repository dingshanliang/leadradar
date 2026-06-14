export function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin}分钟前`;
  if (diffHour < 24) return `${diffHour}小时前`;
  if (diffDay < 7) return `${diffDay}天前`;

  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function formatBudget(amount: number | null): string {
  if (amount == null) return "-";
  if (amount >= 10000) return `${(amount / 10000).toFixed(0)}万`;
  return amount.toLocaleString("zh-CN");
}

export function formatDueTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const isPast = diffMs < 0;
  const absMin = Math.floor(Math.abs(diffMs) / 60000);
  const absHour = Math.floor(Math.abs(diffMs) / 3600000);
  const absDay = Math.floor(Math.abs(diffMs) / 86400000);

  if (absMin < 1) return isPast ? "刚刚到期" : "即将到期";
  if (absHour < 1) return isPast ? `${absMin}分钟前到期` : `${absMin}分钟后到期`;
  if (absDay < 1) return isPast ? `${absHour}小时前到期` : `${absHour}小时后到期`;
  if (absDay < 7) return isPast ? `${absDay}天前到期` : `${absDay}天后到期`;

  return d.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

/** Format a Date as `YYYY-MM-DDTHH:mm` for `<input type="datetime-local" step="3600">`. */
export function formatDateTimeLocal(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/**
 * Parse a suggestion duration such as `2h`, `1d`, `7d`, `1w`.
 * Returns duration in milliseconds, or `null` if invalid.
 */
export function parseSuggestionDuration(value: string): number | null {
  const match = value.trim().match(/^(\d+)\s*([hdw])$/i);
  if (!match) return null;
  const amount = parseInt(match[1], 10);
  const unit = match[2].toLowerCase();
  const multipliers: Record<string, number> = {
    h: 60 * 60 * 1000,
    d: 24 * 60 * 60 * 1000,
    w: 7 * 24 * 60 * 60 * 1000,
  };
  return amount * multipliers[unit];
}
