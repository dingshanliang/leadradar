import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: string;
  className?: string;
}

export function MetricCard({ label, value, trend, className }: MetricCardProps) {
  return (
    <div className={cn("p-4 bg-white rounded-xl border border-border", className)}>
      <p className="text-xs text-muted font-medium">{label}</p>
      <p className="text-2xl font-bold font-mono text-primary mt-1">{value}</p>
      {trend && <p className="text-xs text-emerald-600 mt-1">{trend}</p>}
    </div>
  );
}
