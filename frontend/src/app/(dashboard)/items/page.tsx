"use client";

import React, { useState, useEffect } from "react";
import { Package, Plus, RefreshCw, Layers, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { ItemCatalog } from "@/components/procurement/item-catalog";
import { useAppAuth } from "@/lib/auth/clerk-adapter";
import { useUserStore } from "@/lib/store/user-store";

export default function ItemsPage() {
  const { getToken } = useAppAuth();
  const orgId = useUserStore((s) => s.orgId);

  const [totalCount, setTotalCount] = useState(0);
  const [activeCount, setActiveCount] = useState(0);
  const [categoriesCount, setCategoriesCount] = useState(0);

  const handleItemsLoaded = React.useCallback((items: any[]) => {
    setTotalCount(items.length);
    setActiveCount(items.filter((i) => i.is_active).length);
    const cats = new Set(items.map((i) => i.category || "General"));
    setCategoriesCount(cats.size);
  }, []);

  return (
    <div className="flex-1 space-y-6 p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 flex items-center gap-2">
            <Package className="h-6 w-6 text-[#FA651E]" />
            Item Catalog &amp; Material Master
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Standard parts, raw materials, units of measure, and default pricing for requisitions and purchase orders.
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Catalog Items"
          value={totalCount}
          subtitle="Registered item codes"
          icon={<Package className="h-4 w-4 text-[#FA651E]" />}
          accent="default"
        />
        <MetricCard
          title="Active Items"
          value={activeCount}
          subtitle="Available for requisitioning"
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />}
          accent="emerald"
        />
        <MetricCard
          title="Taxonomy Categories"
          value={categoriesCount}
          subtitle="Active material groups"
          icon={<Layers className="h-4 w-4 text-blue-500" />}
          accent="blue"
        />
      </div>

      {/* Main Component */}
      <ItemCatalog onItemsLoaded={handleItemsLoaded} />
    </div>
  );
}
