import { Skeleton } from "@/components/ui/skeleton";

export function DashboardSkeleton() {
  return (
    <>
      <div className="grid grid-cols-6 gap-4 mb-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-[310px]" />
        <Skeleton className="h-[310px]" />
        <Skeleton className="h-[200px] col-span-2" />
      </div>
    </>
  );
}

export default function Loading() {
  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        信号看板
      </h1>
      <p className="text-sm text-muted mb-6">数据概览与分布分析</p>
      <DashboardSkeleton />
    </div>
  );
}
