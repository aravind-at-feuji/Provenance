"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Database,
  RefreshCw,
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Play,
  RotateCcw,
  Search,
  FileText,
  Shield,
  Layers,
  ChevronRight,
  Info,
} from "lucide-react";
import { useUserStore } from "@/lib/store/user-store";
import { useAppAuth } from "@/lib/auth/clerk-adapter";
import { MetricCard } from "@/components/ui/metric-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface DataSourceItem {
  id: string;
  source_key: string;
  name: string;
  source_type: string;
  base_url?: string | null;
  auth_type?: string | null;
  reliability: string;
  is_enabled: boolean;
  status: "healthy" | "degraded" | "failed" | string;
  poll_interval_seconds?: number | null;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  consecutive_failures: number;
  license_terms?: string | null;
  terms_verified_at?: string | null;
  coverage_notes?: string | null;
  config?: Record<string, unknown>;
}

interface DLQItem {
  id: string;
  task_name: string;
  payload: Record<string, unknown>;
  error?: string | null;
  traceback?: string | null;
  retry_count: number;
  status: string;
  created_at: string;
  replayed_at?: string | null;
  replayed_by?: string | null;
}

interface EventItem {
  id: string;
  event_type: string;
  summary: string;
  severity_signal?: string | null;
  published_date?: string | null;
  effective_date?: string | null;
  jurisdictions?: string[];
  corroboration_count?: number;
}

export default function DataSourcesPage(): React.JSX.Element {
  const orgId = useUserStore((s) => s.orgId);
  const { getToken } = useAppAuth();

  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [dlqEntries, setDlqEntries] = useState<DLQItem[]>([]);
  const [recentEvents, setRecentEvents] = useState<EventItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"connectors" | "dlq" | "events">("connectors");
  const [pollingSourceId, setPollingSourceId] = useState<string | null>(null);
  const [replayingDlqId, setReplayingDlqId] = useState<string | null>(null);

  // Modal inspection
  const [selectedSource, setSelectedSource] = useState<DataSourceItem | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (orgId) headers["x-org-id"] = orgId;

      // 1. Fetch live data sources connectors
      const srcRes = await fetch("/api/v1/admin/data-sources", { headers });
      if (srcRes.ok) {
        const srcData = await srcRes.json();
        setSources(Array.isArray(srcData) ? srcData : []);
      } else {
        setSources([]);
      }

      // 2. Fetch dead letter queue entries
      const dlqRes = await fetch("/api/v1/admin/dlq", { headers }).catch(() => null);
      if (dlqRes && dlqRes.ok) {
        const dlqData = await dlqRes.json();
        setDlqEntries(Array.isArray(dlqData) ? dlqData : []);
      } else {
        setDlqEntries([]);
      }

      // 3. Fetch recent ingested events
      const evRes = await fetch("/api/v1/events?limit=10", { headers }).catch(() => null);
      if (evRes && evRes.ok) {
        const evData = await evRes.json();
        setRecentEvents(evData.data || []);
      } else {
        setRecentEvents([]);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load connector telemetry");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, getToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Trigger immediate manual poll for a connector
  const handlePollNow = async (sourceId: string, sourceName: string) => {
    setPollingSourceId(sourceId);
    setActionSuccessMsg(null);
    setErrorMsg(null);
    try {
      const token = await getToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (orgId) headers["x-org-id"] = orgId;

      const res = await fetch(`/api/v1/admin/data-sources/${sourceId}/poll`, {
        method: "POST",
        headers,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Manual poll failed to execute");
      }

      const summary = await res.json();
      setActionSuccessMsg(
        `Polled ${sourceName}: ${summary.total_fetched ?? 0} fetched (${summary.new_records ?? 0} new records, ${summary.duplicates ?? 0} duplicates).`
      );
      await loadData();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Manual poll failed");
    } finally {
      setPollingSourceId(null);
    }
  };

  // Replay a failed job from the Dead Letter Queue
  const handleReplayDlq = async (dlqId: string) => {
    setReplayingDlqId(dlqId);
    setActionSuccessMsg(null);
    setErrorMsg(null);
    try {
      const token = await getToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (orgId) headers["x-org-id"] = orgId;

      const res = await fetch(`/api/v1/admin/dlq/${dlqId}/replay`, {
        method: "POST",
        headers,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "DLQ replay failed");
      }

      const result = await res.json();
      setActionSuccessMsg(`Job replayed successfully: ${result.message || "Status updated to replayed"}.`);
      await loadData();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to replay DLQ job");
    } finally {
      setReplayingDlqId(null);
    }
  };

  // Filtered connectors
  const filteredSources = useMemo(() => {
    if (!searchQuery.trim()) return sources;
    const q = searchQuery.toLowerCase();
    return sources.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.source_key.toLowerCase().includes(q) ||
        s.source_type.toLowerCase().includes(q)
    );
  }, [sources, searchQuery]);

  const healthyCount = sources.filter((s) => s.status === "healthy").length;
  const degradedCount = sources.filter((s) => s.status !== "healthy").length;
  const activeDlqCount = dlqEntries.filter((e) => e.status === "failed").length;

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-500 max-w-7xl mx-auto pb-12">
      {/* ── Top Header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-950 font-mono">
            Data Sources &amp; Ingestion Telemetry
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Real-time connector health, polling intervals, and dead letter queue oversight.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
            className="rounded-xl border-neutral-200 text-xs shadow-2xs hover:bg-neutral-50"
          >
            <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isLoading && "animate-spin")} />
            {isLoading ? "Refreshing..." : "Refresh Telemetry"}
          </Button>
        </div>
      </div>

      {/* ── Feedback Banners ────────────────────────────────────────── */}
      {actionSuccessMsg && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionSuccessMsg}</span>
          </div>
          <button
            onClick={() => setActionSuccessMsg(null)}
            className="text-neutral-500 hover:text-neutral-800 text-xs underline ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800">
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

      {/* ── Live Computed Telemetry KPIs ─────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Configured Connectors"
          value={isLoading ? "..." : String(sources.length)}
          subtitle={`${sources.filter((s) => s.is_enabled).length} Enabled Ingestion Feeds`}
          icon={<Database className="h-4 w-4" />}
          accent="blue"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="Connector Health"
          value={isLoading ? "..." : `${healthyCount} Healthy`}
          subtitle={degradedCount > 0 ? `${degradedCount} Degraded / Failed` : "All Services Operating Normally"}
          icon={<Activity className="h-4 w-4" />}
          accent={degradedCount > 0 ? "critical" : "emerald"}
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="Ingested Events Stream"
          value={isLoading ? "..." : String(recentEvents.length)}
          subtitle="Normalized Global Disruption Events"
          icon={<Layers className="h-4 w-4" />}
          accent="high"
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
        <MetricCard
          title="Dead Letter Queue"
          value={isLoading ? "..." : String(activeDlqCount)}
          subtitle={activeDlqCount === 0 ? "Zero Unhandled Job Failures" : "Requires Pipeline Attention"}
          icon={<AlertTriangle className="h-4 w-4" />}
          accent={activeDlqCount > 0 ? "critical" : "default"}
          className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs hover:shadow-sm"
        />
      </div>

      {/* ── Navigation Tabs ─────────────────────────────────────────── */}
      <div className="flex border-b border-neutral-200 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("connectors")}
          className={cn(
            "pb-3 flex items-center gap-2 border-b-2 font-mono transition-colors text-xs",
            activeTab === "connectors"
              ? "border-neutral-900 text-neutral-950 font-bold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          )}
        >
          <Database className="w-3.5 h-3.5" />
          Connectors Registry ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab("dlq")}
          className={cn(
            "pb-3 flex items-center gap-2 border-b-2 font-mono transition-colors text-xs",
            activeTab === "dlq"
              ? "border-neutral-900 text-neutral-950 font-bold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          )}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Dead Letter Queue ({dlqEntries.length})
        </button>
        <button
          onClick={() => setActiveTab("events")}
          className={cn(
            "pb-3 flex items-center gap-2 border-b-2 font-mono transition-colors text-xs",
            activeTab === "events"
              ? "border-neutral-900 text-neutral-950 font-bold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          )}
        >
          <Layers className="w-3.5 h-3.5" />
          Recent Ingested Events ({recentEvents.length})
        </button>
      </div>

      {/* ── TAB 1: Connectors Registry ───────────────────────────────── */}
      {activeTab === "connectors" && (
        <Card className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
          <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-neutral-100 gap-3">
            <div>
              <CardTitle className="text-base text-neutral-950 font-bold">
                External Data Source Connectors
              </CardTitle>
              <CardDescription className="text-xs text-neutral-500">
                Official regulatory feeds, sanctions lists, and trade notice adapters.
              </CardDescription>
            </div>
            <div className="w-full sm:w-64">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-neutral-400" />
                <Input
                  placeholder="Filter connectors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 text-xs rounded-xl border-neutral-200"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {isLoading ? (
              <div className="py-12 text-center text-xs text-neutral-400">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#FA651E]" />
                Querying data source telemetry...
              </div>
            ) : filteredSources.length === 0 ? (
              <div className="py-12 text-center text-neutral-500 space-y-2">
                <Database className="h-8 w-8 text-neutral-400 mx-auto" />
                <p className="text-sm font-semibold text-neutral-900">No Data Sources Found</p>
                <p className="text-xs max-w-sm mx-auto text-neutral-500">
                  {searchQuery
                    ? "No data source connectors matched your search term."
                    : "No data sources are currently seeded in the database."}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredSources.map((source) => (
                  <div
                    key={source.id}
                    className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-xl border border-neutral-200/70 bg-neutral-50/50 hover:bg-neutral-100/50 transition-colors"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          variant={
                            source.status === "healthy"
                              ? "default"
                              : source.status === "degraded"
                              ? "high"
                              : "critical"
                          }
                          className="text-[10px] uppercase font-mono px-2"
                        >
                          {source.status}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px] font-mono px-2 bg-neutral-200/80">
                          {source.source_type.replace("_", " ")}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] font-mono px-2 border-neutral-300">
                          Reliability: {source.reliability}
                        </Badge>
                        {source.consecutive_failures > 0 && (
                          <span className="text-[10px] font-mono text-rose-600 font-semibold">
                            {source.consecutive_failures} failures
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-bold text-neutral-900">{source.name}</h3>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-500">
                        <span className="font-mono text-[11px] text-neutral-700">key: {source.source_key}</span>
                        {source.poll_interval_seconds && (
                          <span>
                            Poll interval:{" "}
                            <strong className="text-neutral-800">
                              {source.poll_interval_seconds >= 3600
                                ? `${Math.round(source.poll_interval_seconds / 3600)}h`
                                : `${Math.round(source.poll_interval_seconds / 60)}m`}
                            </strong>
                          </span>
                        )}
                        <span>
                          Last success:{" "}
                          <strong className="text-neutral-800">
                            {source.last_success_at
                              ? new Date(source.last_success_at).toLocaleString()
                              : "Pending first run"}
                          </strong>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end lg:self-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedSource(source)}
                        className="rounded-xl border-neutral-200 bg-white text-xs hover:bg-neutral-50 shadow-2xs"
                      >
                        <Info className="mr-1.5 h-3.5 w-3.5" />
                        Details
                      </Button>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handlePollNow(source.id, source.name)}
                        disabled={pollingSourceId === source.id}
                        className="rounded-xl bg-neutral-900 text-white text-xs hover:bg-neutral-800 shadow-2xs"
                      >
                        <Play className={cn("mr-1.5 h-3.5 w-3.5", pollingSourceId === source.id && "animate-spin")} />
                        {pollingSourceId === source.id ? "Polling..." : "Poll Now"}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── TAB 2: Dead Letter Queue (DLQ) ───────────────────────────── */}
      {activeTab === "dlq" && (
        <Card className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
          <CardHeader className="pb-4 border-b border-neutral-100">
            <CardTitle className="text-base text-neutral-950 font-bold">
              Dead Letter Queue (DLQ) Oversight
            </CardTitle>
            <CardDescription className="text-xs text-neutral-500">
              Failed background ingestion tasks preserved for inspection, debugging, and safe replay.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {isLoading ? (
              <div className="py-12 text-center text-xs text-neutral-400">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#FA651E]" />
                Checking Dead Letter Queue...
              </div>
            ) : dlqEntries.length === 0 ? (
              <div className="py-12 text-center text-neutral-500 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
                <p className="text-sm font-semibold text-neutral-900">Dead Letter Queue is Clean</p>
                <p className="text-xs max-w-sm mx-auto text-neutral-500">
                  No failed ingestion jobs recorded. Ingestion pipelines and normalization stages are operating without errors.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {dlqEntries.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 p-4 rounded-xl border border-neutral-200/70 bg-neutral-50/50"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={entry.status === "failed" ? "critical" : "secondary"}
                          className="text-[10px] font-mono px-2"
                        >
                          {entry.status}
                        </Badge>
                        <span className="font-mono text-xs font-bold text-neutral-900">{entry.task_name}</span>
                        <span className="text-xs text-neutral-400">· Retry count: {entry.retry_count}</span>
                      </div>
                      <p className="text-xs text-rose-700 font-mono bg-rose-50/60 p-2 rounded border border-rose-200/50 max-w-2xl break-all">
                        {entry.error || "Unknown execution exception"}
                      </p>
                      <span className="text-[11px] text-neutral-400">
                        Queued: {new Date(entry.created_at).toLocaleString()}
                      </span>
                    </div>

                    <div className="self-end lg:self-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReplayDlq(entry.id)}
                        disabled={replayingDlqId === entry.id || entry.status === "replayed"}
                        className="rounded-xl border-neutral-200 text-xs shadow-2xs hover:bg-neutral-50"
                      >
                        <RotateCcw className={cn("mr-1.5 h-3.5 w-3.5", replayingDlqId === entry.id && "animate-spin")} />
                        {replayingDlqId === entry.id ? "Replaying..." : entry.status === "replayed" ? "Replayed" : "Replay Job"}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── TAB 3: Recent Ingested Events ────────────────────────────── */}
      {activeTab === "events" && (
        <Card className="rounded-2xl border-neutral-200/80 bg-white shadow-2xs">
          <CardHeader className="pb-4 border-b border-neutral-100">
            <CardTitle className="text-base text-neutral-950 font-bold">
              Recently Ingested Disruption Events
            </CardTitle>
            <CardDescription className="text-xs text-neutral-500">
              Normalized events extracted from external regulatory feeds and trade notices.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {isLoading ? (
              <div className="py-12 text-center text-xs text-neutral-400">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#FA651E]" />
                Fetching event telemetry...
              </div>
            ) : recentEvents.length === 0 ? (
              <div className="py-12 text-center text-neutral-500 space-y-2">
                <Layers className="h-8 w-8 text-neutral-400 mx-auto" />
                <p className="text-sm font-semibold text-neutral-900">No Events Ingested Yet</p>
                <p className="text-xs max-w-sm mx-auto text-neutral-500">
                  Trigger an ingestion poll on any connector above to fetch and normalize live external notices.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3.5 rounded-xl border border-neutral-200/70 bg-neutral-50/50 space-y-1.5"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary" className="text-[10px] font-mono px-2 bg-neutral-200">
                        {ev.event_type}
                      </Badge>
                      {ev.severity_signal && (
                        <Badge
                          variant={ev.severity_signal === "severe" ? "critical" : "high"}
                          className="text-[10px] font-mono px-2 uppercase"
                        >
                          {ev.severity_signal}
                        </Badge>
                      )}
                      {ev.jurisdictions && ev.jurisdictions.length > 0 && (
                        <span className="text-[11px] font-mono text-neutral-500">
                          Jurisdictions: {ev.jurisdictions.join(", ")}
                        </span>
                      )}
                      {ev.corroboration_count && ev.corroboration_count > 1 && (
                        <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                          {ev.corroboration_count} sources
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-medium text-neutral-900">{ev.summary}</p>
                    <div className="text-[11px] text-neutral-400">
                      {ev.effective_date && <span>Effective: {ev.effective_date} · </span>}
                      {ev.published_date && <span>Published: {ev.published_date}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Connector Details Inspection Modal ──────────────────────── */}
      <Dialog open={!!selectedSource} onOpenChange={() => setSelectedSource(null)}>
        <DialogContent className="max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-base font-bold font-mono">
              {selectedSource?.name}
            </DialogTitle>
            <DialogDescription className="text-xs text-neutral-500">
              Detailed configuration and legal provenance terms.
            </DialogDescription>
          </DialogHeader>

          {selectedSource && (
            <div className="space-y-4 py-2 text-xs">
              <div>
                <span className="font-semibold text-neutral-700">Machine Key</span>
                <p className="font-mono text-neutral-900 mt-0.5">{selectedSource.source_key}</p>
              </div>

              {selectedSource.base_url && (
                <div>
                  <span className="font-semibold text-neutral-700">Base URL</span>
                  <p className="font-mono text-neutral-900 break-all mt-0.5">{selectedSource.base_url}</p>
                </div>
              )}

              {selectedSource.coverage_notes && (
                <div>
                  <span className="font-semibold text-neutral-700">Coverage Notes</span>
                  <p className="text-neutral-600 mt-0.5 leading-relaxed">{selectedSource.coverage_notes}</p>
                </div>
              )}

              {selectedSource.license_terms && (
                <div>
                  <span className="font-semibold text-neutral-700">Licensing &amp; Provenance</span>
                  <p className="text-neutral-600 mt-0.5 leading-relaxed bg-neutral-50 p-2.5 rounded-lg border border-neutral-200/60 font-mono text-[11px]">
                    {selectedSource.license_terms}
                  </p>
                </div>
              )}

              {selectedSource.terms_verified_at && (
                <div>
                  <span className="font-semibold text-neutral-700">Terms Last Verified</span>
                  <p className="text-neutral-600 mt-0.5 font-mono">{selectedSource.terms_verified_at}</p>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedSource(null)}
              className="rounded-xl border-neutral-200 text-xs"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
