import { cn } from "@/lib/utils";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export function Card({ title, children, className, padding = true }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-bg-elevated",
        padding && "p-6",
        className
      )}
    >
      {title && (
        <h3 className="font-heading text-sm font-semibold text-secondary mb-4 uppercase tracking-wide">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
