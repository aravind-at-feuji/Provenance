"use client";

import React from "react";
import { cn } from "@/lib/utils";

export type ProcurementDocumentStatus =
  | "draft"
  | "pending_approval"
  | "pending"
  | "approved"
  | "ordered"
  | "partially_ordered"
  | "cancelled"
  | "rejected"
  | "active"
  | "inactive";

interface DocumentStatusBadgeProps {
  status: string;
  className?: string;
  size?: "sm" | "md";
}

export function DocumentStatusBadge({
  status,
  className,
  size = "md",
}: DocumentStatusBadgeProps) {
  const normalized = (status || "").toLowerCase().trim();

  let label = status.replace(/_/g, " ");
  // Capitalize words
  label = label.replace(/\b\w/g, (c) => c.toUpperCase());

  let styleClasses = "bg-neutral-100 text-neutral-700 border-neutral-200";

  switch (normalized) {
    case "draft":
      styleClasses = "bg-neutral-100 text-neutral-700 border-neutral-300";
      break;
    case "pending_approval":
    case "pending":
      styleClasses = "bg-amber-50 text-amber-700 border-amber-200/80 font-medium";
      break;
    case "approved":
      styleClasses = "bg-emerald-50 text-emerald-700 border-emerald-200/80 font-medium";
      break;
    case "ordered":
      styleClasses = "bg-blue-50 text-blue-700 border-blue-200/80 font-medium";
      break;
    case "partially_ordered":
      styleClasses = "bg-indigo-50 text-indigo-700 border-indigo-200/80 font-medium";
      break;
    case "rejected":
    case "cancelled":
      styleClasses = "bg-rose-50 text-rose-700 border-rose-200/80 font-medium";
      break;
    case "active":
      styleClasses = "bg-emerald-50 text-emerald-700 border-emerald-200/80 font-medium";
      break;
    case "inactive":
      styleClasses = "bg-neutral-100 text-neutral-500 border-neutral-200";
      break;
    default:
      styleClasses = "bg-neutral-100 text-neutral-700 border-neutral-200";
      break;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 font-mono uppercase tracking-wide",
        size === "sm" ? "text-[10px] leading-tight" : "text-xs font-semibold",
        styleClasses,
        className
      )}
    >
      {label}
    </span>
  );
}

interface PriorityBadgeProps {
  priority: string;
  className?: string;
}

export function PriorityBadge({ priority, className }: PriorityBadgeProps) {
  const norm = (priority || "").toLowerCase();
  let styleClasses = "bg-neutral-100 text-neutral-700 border-neutral-200";

  switch (norm) {
    case "critical":
      styleClasses = "bg-red-50 text-red-700 border-red-200 font-bold";
      break;
    case "high":
      styleClasses = "bg-orange-50 text-orange-700 border-orange-200 font-semibold";
      break;
    case "medium":
      styleClasses = "bg-amber-50 text-amber-700 border-amber-200";
      break;
    case "low":
      styleClasses = "bg-neutral-100 text-neutral-600 border-neutral-200";
      break;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-mono capitalize",
        styleClasses,
        className
      )}
    >
      {priority}
    </span>
  );
}
