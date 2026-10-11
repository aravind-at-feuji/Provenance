"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Building2,
  DollarSign,
  Activity,
  Sparkles,
  Layers,
  ChevronRight,
  Eye,
  RefreshCw,
  Globe,
  CheckCircle2,
  Gauge,
  ArrowRight,
} from "lucide-react";
import { useUserStore } from "@/lib/store/user-store";
import { useAppAuth } from "@/lib/auth/clerk-adapter";
import { MetricCard } from "@/components/ui/metric-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface SupplierItem {
  id: string;
  org_id: string;
  company_id: string;
  relationship_type: string;
  tier: number | null;
  criticality: number | null;
  annual_spend_usd: number | null;
  category: string | null;
  single_source: boolean;
  lead_time_days: number | null;
  confidence: number;
  source: string;
  company: {
    id: string;
    legal_name: string;
    country: string | null;
    is_verified?: boolean;
    primary_domain?: string | null;
  };
}

interface ReviewItem {
  id: string;
  status: string;
}

export default function DashboardPage(): React.JSX.Element {
  const orgId = useUserStore((s) => s.orgId);
  const { getToken } = useAppAuth();

  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [pendingReviews, setPendingReviews] = useState<ReviewItem[]>([]);
  const [healthStatus, setHealthStatus] = useState<string>("ok");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [filterScope, setFilterScope] = useState<"all" | "tier1" | "subtier">("all");

  const loadDashboardData = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (orgId) headers["x-org-id"] = orgId;

      // 1. Fetch live suppliers
      const supRes = await fetch("/api/v1/suppliers?limit=100", { headers });
      if (supRes.ok) {
        const supData = await supRes.json();
        setSuppliers(supData.data || []);
      } else {
        setSuppliers([]);
      }

      // 2. Fetch pending entity reviews
      const revRes = await fetch("/api/v1/entity-reviews?status=pending", { headers }).catch(() => null);
      if (revRes && revRes.ok) {
        const revData = await revRes.json();
        setPendingReviews(revData.data || []);
      } else {
        setPendingReviews([]);
      }

      // 3. Fetch system health
      const hRes = await fetch("/api/v1/health").catch(() => null);
      if (hRes && hRes.ok) {
        const hData = await hRes.json();
        setHealthStatus(hData.status === "ok" ? "Operational" : "Degraded");
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load dashboard intelligence");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, getToken]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Computed metrics from real database entities
  const computed = useMemo(() => {
    const totalSuppliers = suppliers.length;
    const tier1Count = suppliers.filter((s) => s.tier === 1).length;
    const subTierCount = suppliers.filter((s) => s.tier && s.tier > 1).length;
    const criticalSuppliers = suppliers.filter((s) => (s.criticality ?? 0) >= 4);
    const singleSourceCount = suppliers.filter((s) => s.single_source).length;
    const totalSpend = suppliers.reduce((acc, s) => acc + (s.annual_spend_usd || 0), 0);

    // Dynamic country breakdown from real companies
    const countryMap: Record<string, number> = {};
    suppliers.forEach((s) => {
      const c = s.company.country || "Other";
      countryMap[c] = (countryMap[c] || 0) + 1;
    });

    const countryBreakdown = Object.entries(countryMap)
      .map(([country, count]) => ({
        country,
        count,
        percentage: totalSuppliers > 0 ? Math.round((count / totalSuppliers) * 100) : 0,
      }))
      .sort((a, b) => b.count - a.count);

    return {
      totalSuppliers,
      tier1Count,
      subTierCount,
      criticalCount: criticalSuppliers.length,
      criticalSuppliers,
      singleSourceCount,
      totalSpend,
      countryBreakdown,
    };
  }, [suppliers]);

  // Filtered suppliers based on segmented control
  const filteredCriticalSuppliers = useMemo(() => {
    if (filterScope === "tier1") {
      return computed.criticalSuppliers.filter((s) => s.tier === 1);
    }
    if (filterScope === "subtier") {
      return computed.criticalSuppliers.filter((s) => s.tier && s.tier > 1);
    }
    return computed.criticalSuppliers;
  }, [computed.criticalSuppliers, filterScope]);

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-500 max-w-7xl mx-auto pb-12">
      {errorMsg && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-neutral-500 hover:text-neutral-800 text-xs underline ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── KPI Row Computed from Live Database ──────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Monitored Suppliers"
          value={isLoading ? "..." : String(computed.totalSuppliers)}
          subtitle={`${computed.tier1Count} Tier-1 · ${computed.subTierCount} Sub-tier`}
          icon={<Gauge className="h-4 w-4" />}
          accent="blue"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="High Criticality Nodes"
          value={isLoading ? "..." : String(computed.criticalCount)}
          subtitle={`${computed.singleSourceCount} single-source dependencies`}
          icon={<AlertTriangle className="h-4 w-4" />}
          accent="critical"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="Total Contract Spend"
          value={isLoading ? "..." : `$${(computed.totalSpend / 1000000).toFixed(2)}M`}
          subtitle={`Across ${computed.countryBreakdown.length} jurisdictions`}
          icon={<DollarSign className="h-4 w-4" />}
          accent="high"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="Pending Entity Reviews"
          value={isLoading ? "..." : String(pendingReviews.length)}
          subtitle={healthStatus === "Operational" ? "Backend Services Healthy" : "System Degraded"}
          icon={<Activity className="h-4 w-4" />}
          accent="emerald"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
      </div>

      {/* ── High Exposure Critical Suppliers from Live Database ───────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Suppliers with Highest Risk Exposure */}
        <Card className="lg:col-span-2 rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
          <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-neutral-100">
            <div>
              <CardTitle className="text-base text-neutral-950 font-bold">
                High-Exposure Supplier Registry
              </CardTitle>
              <CardDescription className="text-xs text-neutral-500">
                Tier-1 and Tier-2 suppliers with Criticality 4 or 5 requiring proactive risk monitoring.
              </CardDescription>
            </div>
            <Button asChild variant="ghost" size="sm" className="rounded-lg text-neutral-600 hover:text-neutral-900">
              <Link href="/suppliers" className="text-xs">
                View all ({computed.totalSuppliers}) <ChevronRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-neutral-400">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#FA651E]" />
                Loading live supplier risk telemetry...
              </div>
            ) : filteredCriticalSuppliers.length === 0 ? (
              <div className="py-10 text-center text-neutral-500 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
                <p className="text-sm font-semibold text-neutral-900">No Critical Exposures in View</p>
                <p className="text-xs max-w-sm mx-auto text-neutral-500">
                  All active suppliers in your registry are currently classified below Criticality 4, or no suppliers have been registered yet.
                </p>
                <Button asChild size="sm" variant="outline" className="mt-3 rounded-xl border-neutral-200">
                  <Link href="/suppliers">Add Suppliers to Registry</Link>
                </Button>
              </div>
            ) : (
              filteredCriticalSuppliers.slice(0, 5).map((sup) => (
                <div
                  key={sup.id}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-neutral-200/70 bg-neutral-50/50 p-3.5 transition-all hover:bg-neutral-100/60 hover:border-neutral-300"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="critical" className="rounded-full px-2 text-[10px]">
                        CRITICALITY {sup.criticality}/5
                      </Badge>
                      <Badge variant="secondary" className="rounded-full px-2 text-[10px] bg-neutral-200/80">
                        TIER {sup.tier ?? 1}
                      </Badge>
                      {sup.single_source && (
                        <Badge variant="outline" className="rounded-full px-2 text-[10px] border-rose-300 text-rose-600 bg-rose-50">
                          SINGLE SOURCE
                        </Badge>
                      )}
                      <span className="text-[11px] font-mono text-neutral-500">
                        {sup.company.country || "Global"}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-neutral-900 group-hover:text-[#FA651E] transition-colors">
                      {sup.company.legal_name}
                    </h3>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-500">
                      <span>
                        Category: <strong className="text-neutral-800">{sup.category || "Unassigned"}</strong>
                      </span>
                      {sup.annual_spend_usd !== null && sup.annual_spend_usd > 0 && (
                        <span>
                          Spend: <strong className="text-neutral-800">${sup.annual_spend_usd.toLocaleString()}</strong>
                        </span>
                      )}
                      <span className="text-[11px]">
                        Source: {sup.source}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 self-end sm:self-center">
                    <Button asChild variant="outline" size="sm" className="rounded-xl border-neutral-200 bg-white hover:bg-neutral-50 shadow-2xs">
                      <Link href={`/suppliers?search=${encodeURIComponent(sup.company.legal_name)}`}>
                        <Eye className="mr-1.5 h-3.5 w-3.5" />
                        View Dossier
                      </Link>
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Live Jurisdictional Exposure Radar */}
        <div className="space-y-6">
          <Card className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
            <CardHeader className="pb-3 border-b border-neutral-100">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-neutral-950 font-bold">
                  Jurisdictional Exposure &amp; Sourcing
                </CardTitle>
                <Badge variant="secondary" className="capitalize text-[10px] rounded-full">
                  Live Registry
                </Badge>
              </div>
              <CardDescription className="text-xs text-neutral-500">
                Geographic concentration across registered suppliers.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5 pt-4 text-xs">
              {computed.countryBreakdown.length === 0 ? (
                <div className="py-6 text-center text-neutral-400">
                  <Globe className="h-6 w-6 mx-auto mb-2 text-neutral-400" />
                  <p className="text-xs">No supplier jurisdictions mapped yet.</p>
                </div>
              ) : (
                computed.countryBreakdown.slice(0, 4).map((item) => (
                  <div key={item.country} className="space-y-1.5">
                    <div className="flex justify-between font-medium text-neutral-700">
                      <span>Jurisdiction: {item.country}</span>
                      <span className="font-mono text-[#FA651E] font-semibold">
                        {item.percentage}% ({item.count} suppliers)
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-neutral-100 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#FA651E] to-[#E03368] rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(item.percentage, 4)}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
              <div className="pt-2">
                <Button asChild variant="outline" size="sm" className="w-full rounded-xl border-neutral-200 bg-white hover:bg-neutral-50 shadow-2xs">
                  <Link href="/graph">
                    <Layers className="mr-1.5 h-3.5 w-3.5" />
                    Explore Network Topology
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Links & Review Queue */}
          <Card className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
            <CardHeader className="pb-2 border-b border-neutral-100">
              <CardTitle className="text-xs uppercase tracking-wider text-neutral-500 font-bold font-mono">
                Action Items &amp; Review Queue
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pt-3 text-xs">
              <div className="flex justify-between items-center py-1.5 border-b border-neutral-100">
                <span className="text-neutral-600">Pending Entity Matches</span>
                <Badge variant={pendingReviews.length > 0 ? "high" : "secondary"} className="rounded-full px-2">
                  {pendingReviews.length} to review
                </Badge>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-neutral-100">
                <span className="text-neutral-600">Single-Source Points</span>
                <span className="font-semibold text-neutral-900">{computed.singleSourceCount} suppliers</span>
              </div>
              <div className="pt-2">
                <Button asChild variant="default" size="sm" className="w-full text-xs rounded-xl bg-neutral-900 hover:bg-neutral-800 text-white shadow-2xs">
                  <Link href="/suppliers/reviews">
                    Resolve Entity Matches ({pendingReviews.length})
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

