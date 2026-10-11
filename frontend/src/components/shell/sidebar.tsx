"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Gauge,
  Compass,
  Network,
  Sparkles,
  Building2,
  AlertTriangle,
  LineChart,
  Settings,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Bell,
  HelpCircle,
  BookOpen,
  Lock,
  ChevronDown,
} from "lucide-react";
import { useUIStore } from "@/lib/store/ui-store";
import { useUserStore } from "@/lib/store/user-store";
import { useAppAuth } from "@/lib/auth/clerk-adapter";
import { ProvenanceLogo } from "@/components/landing/ProvenanceLogo";
import { UserMenu } from "./user-menu";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  badgeVariant?: "critical" | "high" | "default" | "secondary" | "ai";
  adminOnly?: boolean;
}

export function Sidebar() {
  const pathname = usePathname();
  const isCollapsed = useUIStore((s) => s.isSidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const isPlatformAdmin = useUserStore((s) => s.isPlatformAdmin);
  const isOnboarded = useUserStore((s) => s.isOnboarded);
  const orgId = useUserStore((s) => s.orgId);
  const { getToken } = useAppAuth();
  const [activeAlertsCount, setActiveAlertsCount] = useState<number | null>(null);
  const [settingsExpanded, setSettingsExpanded] = useState(false);

  React.useEffect(() => {
    let isMounted = true;
    async function fetchCounts() {
      if (!orgId) return;
      try {
        const token = await getToken();
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;
        if (orgId) headers["x-org-id"] = orgId;
        const res = await fetch("/api/v1/alerts/counts", { headers });
        if (res.ok && isMounted) {
          const data = await res.json();
          const unhandled = (data.new ?? 0) + (data.acknowledged ?? 0);
          setActiveAlertsCount(unhandled > 0 ? unhandled : null);
        }
      } catch {
        // silent fallback
      }
    }
    fetchCounts();
  }, [orgId, getToken, pathname]);

  const navItems: NavItem[] = [
    {
      title: "Dashboard",
      href: "/dashboard",
      icon: Gauge,
    },
    {
      title: "Onboarding",
      href: "/onboarding",
      icon: Compass,
      badge: !isOnboarded ? "Setup" : undefined,
      badgeVariant: "high",
    },
    {
      title: "Alerts",
      href: "/alerts",
      icon: AlertTriangle,
      badge: activeAlertsCount && activeAlertsCount > 0 ? activeAlertsCount : undefined,
      badgeVariant: "critical",
    },
    {
      title: "Suppliers",
      href: "/suppliers",
      icon: Building2,
    },
    {
      title: "Graph",
      href: "/graph",
      icon: Network,
    },
    {
      title: "Investigate",
      href: "/investigate",
      icon: Sparkles,
      badge: "AI",
      badgeVariant: "ai",
    },
    {
      title: "Data",
      href: "/data",
      icon: LineChart,
    },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col h-full shrink-0 border-r border-neutral-200/80 bg-white transition-all duration-300 z-30 select-none shadow-[1px_0_4px_rgba(0,0,0,0.02)]",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-neutral-100 px-3.5">
        {!isCollapsed ? (
          <>
            <Link href="/dashboard" className="flex items-center gap-2 pl-1 group">
              <ProvenanceLogo size="sm" inverted={false} withTagline={false} />
              <span className="text-xs font-extrabold tracking-wider text-neutral-900 font-mono">
                PROVENANCE
              </span>
            </Link>
            <div className="flex items-center gap-1">
              {/* Notification Bell */}
              <Link
                href="/alerts"
                className="relative p-1.5 text-neutral-500 hover:text-neutral-900 rounded-lg hover:bg-neutral-100 transition-colors"
                title="Active Alerts"
              >
                <Bell className="w-4 h-4" />
                {activeAlertsCount && activeAlertsCount > 0 ? (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#FA651E] ring-2 ring-white" />
                ) : null}
              </Link>
              {/* Collapse Button */}
              <button
                onClick={toggleSidebar}
                className="p-1.5 text-neutral-400 hover:text-neutral-800 rounded-lg hover:bg-neutral-100 transition-colors"
                aria-label="Collapse sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center p-1.5 text-neutral-500 hover:text-neutral-900 rounded-lg hover:bg-neutral-100 transition-colors"
            aria-label="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-1">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2 text-xs transition-all duration-150",
                isActive
                  ? "bg-neutral-100 text-neutral-950 font-semibold shadow-2xs border border-neutral-200/60"
                  : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950 font-medium"
              )}
              title={isCollapsed ? item.title : undefined}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-transform group-hover:scale-105",
                  isActive ? "text-[#FA651E]" : "text-neutral-500"
                )}
              />
              {!isCollapsed && (
                <span className="flex-1 truncate tracking-tight">{item.title}</span>
              )}
              {!isCollapsed && item.badge && (
                item.badgeVariant === "ai" ? (
                  <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-[#FA651E]/10 text-[#FA651E] border border-[#FA651E]/20 font-mono">
                    {item.badge}
                  </span>
                ) : (
                  <Badge
                    variant={item.badgeVariant ?? "secondary"}
                    className="ml-auto text-[10px] py-0 px-1.5 font-mono"
                  >
                    {item.badge}
                  </Badge>
                )
              )}
            </Link>
          );
        })}

        {/* Collapsible Settings Group (Gojiberry Style) */}
        {!isCollapsed ? (
          <div className="pt-1">
            <button
              onClick={() => setSettingsExpanded(!settingsExpanded)}
              className={cn(
                "w-full flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium transition-all duration-150 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950",
                pathname.startsWith("/settings") && "text-neutral-950 font-semibold"
              )}
            >
              <div className="flex items-center gap-3">
                <Settings className="h-4 w-4 text-neutral-500" />
                <span>Settings</span>
              </div>
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 text-neutral-400 transition-transform duration-200",
                  settingsExpanded && "rotate-180"
                )}
              />
            </button>

            {settingsExpanded && (
              <div className="pl-9 pr-2 py-1 space-y-1 animate-in fade-in duration-200">
                <Link
                  href="/settings"
                  className={cn(
                    "block py-1.5 px-2 text-[11px] rounded-lg transition-colors",
                    pathname === "/settings"
                      ? "text-[#FA651E] font-semibold bg-orange-50/50"
                      : "text-neutral-500 hover:text-neutral-900"
                  )}
                >
                  Account &amp; Organization
                </Link>
                <Link
                  href="/settings#integrations"
                  className="block py-1.5 px-2 text-[11px] text-neutral-500 hover:text-neutral-900 rounded-lg transition-colors"
                >
                  ERP &amp; API Integrations
                </Link>
              </div>
            )}
          </div>
        ) : (
          <Link
            href="/settings"
            className="flex items-center justify-center p-2 rounded-xl text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 transition-colors"
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </Link>
        )}

        {/* Platform Admin */}
        {isPlatformAdmin && (
          <Link
            href="/admin"
            className={cn(
              "group flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all duration-150",
              pathname.startsWith("/admin")
                ? "bg-neutral-100 text-neutral-950 font-semibold border border-neutral-200/60"
                : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950"
            )}
            title={isCollapsed ? "Platform Admin" : undefined}
          >
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            {!isCollapsed && <span className="flex-1 truncate">Platform Admin</span>}
          </Link>
        )}
      </div>

      {/* Bottom User Profile Section */}
      <div className="shrink-0 border-t border-neutral-100 p-2 bg-neutral-50/40">
        <UserMenu isCollapsed={isCollapsed} />
      </div>
    </aside>
  );
}
