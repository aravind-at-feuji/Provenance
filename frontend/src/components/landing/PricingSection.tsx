"use client";

import React from "react";
import Link from "next/link";
import { CornerMarks } from "./CornerMarks";
import { Check, ArrowRight } from "lucide-react";

export function PricingSection() {
  const coreFeatures = [
    "Multi-tier supplier graph mapping (up to 500 active vendors)",
    "Continuous ingestion across official Tier-1 regulatory registers",
    "GLEIF Level-2 entity resolution with parent/subsidiary cascade",
    "Deterministic dollar exposure scoring without AI hallucinations",
    "Role-scoped dashboards for Risk Managers & Category Managers",
    "Full evidence chains with verifiable legal gazette citations",
    "30-day retroactive disruption backfill on onboarding",
  ];

  const enterpriseFeatures = [
    "Everything in Enterprise Core",
    "Unlimited supplier graph depth (Tier 1 down to Tier 5 smelters/mines)",
    "Sub-minute real-time regulatory radar with Defcon-1 push alerts",
    "Bi-directional ERP connectors (SAP S/4HANA, Ariba, Coupa, Oracle)",
    "Spend leakage detection with live regulatory overlap flags",
    "AI Conversational Investigation Agent (Agent 4) with custom RAG",
    "Dedicated VPC or on-premises air-gapped deployment option",
    "24/7 Supply Disruption War Room support & dedicated analyst",
  ];

  return (
    <section id="pricing" className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header with Registration Frame */}
        <div className="relative max-w-4xl mx-auto mb-16 p-6 sm:p-8 bg-white/40 rounded-xl border border-neutral-200/60 text-center">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E]" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              Transparent Deployment Tiers
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A] leading-tight mb-4">
            Predictable investment. <br className="hidden sm:inline" />
            <span className="text-[#FA651E]">Millions in disruption spend</span> protected.
          </h2>

          <p className="text-base sm:text-lg text-neutral-600 font-normal">
            Deploy in under 15 minutes. Backfill the last 30 days of global trade shocks today.
          </p>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Card 1: ENTERPRISE CORE */}
          <div className="relative bg-white rounded-2xl border border-neutral-200 p-8 sm:p-10 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all">
            <CornerMarks size={10} color="#a3a3a3" thickness={1.2} offset={-5} />

            <div>
              {/* Badge */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-neutral-100 rounded-md text-xs font-mono font-bold tracking-wider text-neutral-800 mb-6">
                <span>⦿</span>
                <span>ENTERPRISE CORE</span>
              </div>

              {/* Price */}
              <div className="flex items-baseline gap-2 mb-4">
                <span className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A]">
                  $ 2,400
                </span>
                <span className="text-neutral-500 font-medium text-sm">/month (annual billing)</span>
              </div>

              {/* Description */}
              <p className="text-sm text-neutral-600 leading-relaxed mb-6 font-normal">
                For manufacturing &amp; industrial operations with complex direct material supply chains.
              </p>

              {/* Badges */}
              <div className="flex items-center gap-2 mb-8">
                <span className="px-2.5 py-1 rounded bg-[#A7F3D0]/70 text-[#065F46] text-xs font-semibold">
                  Up to 500 Suppliers
                </span>
                <span className="px-2.5 py-1 rounded bg-[#FEF08A] text-[#854D0E] text-xs font-semibold">
                  Continuous Ingestion
                </span>
              </div>

              {/* CTA Button with Arrow Box */}
              <Link
                href="/dashboard"
                className="relative group w-full mb-10 inline-flex items-center bg-white hover:bg-neutral-50 text-neutral-900 border border-neutral-300 rounded-sm shadow-xs transition-all"
              >
                <CornerMarks size={6} color="#FA651E" thickness={1.2} offset={-3} />
                <div className="w-10 h-10 bg-[#FA651E] text-white flex items-center justify-center group-hover:bg-[#E04803] transition-colors shrink-0">
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </div>
                <span className="px-4 py-2.5 text-xs sm:text-sm font-semibold tracking-tight">
                  Launch Live Demo Radar →
                </span>
              </Link>

              {/* Feature Checklist */}
              <div className="border-t border-neutral-100 pt-8">
                <div className="text-xs font-mono uppercase tracking-wider text-neutral-400 font-bold mb-4">
                  What&apos;s included
                </div>
                <ul className="space-y-3.5 text-xs sm:text-sm text-neutral-700">
                  {coreFeatures.map((feat) => (
                    <li key={feat} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Card 2: GLOBAL ENTERPRISE */}
          <div className="relative bg-white rounded-2xl border-2 border-neutral-900 p-8 sm:p-10 shadow-lg flex flex-col justify-between hover:shadow-xl transition-all">
            <CornerMarks size={10} color="#FA651E" thickness={1.5} offset={-5} />

            <div>
              {/* Badge */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#0A0A0A] text-white rounded-md text-xs font-mono font-bold tracking-wider mb-6">
                <span>✦</span>
                <span>GLOBAL ENTERPRISE</span>
              </div>

              {/* Price */}
              <div className="flex items-baseline gap-2 mb-4">
                <span className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A]">
                  Custom
                </span>
                <span className="text-neutral-500 font-medium text-sm">/tailored SLA</span>
              </div>

              {/* Description */}
              <p className="text-sm text-neutral-600 leading-relaxed mb-6 font-normal">
                For Fortune 500 OEMs, defense contractors, and global multi-tier supply networks.
              </p>

              {/* Badges */}
              <div className="flex items-center gap-2 mb-8">
                <span className="px-2.5 py-1 rounded bg-[#FD8A6B]/25 text-[#9A3412] text-xs font-semibold">
                  Unlimited Depth
                </span>
                <span className="px-2.5 py-1 rounded bg-neutral-100 text-neutral-800 text-xs font-semibold">
                  Dedicated VPC / Air-Gapped
                </span>
              </div>

              {/* CTA Button (Solid Dark) */}
              <Link
                href="/dashboard"
                className="relative group w-full mb-10 inline-flex items-center bg-[#0A0A0A] hover:bg-neutral-800 text-white rounded-sm shadow-md transition-all"
              >
                <CornerMarks size={6} color="#FA651E" thickness={1.2} offset={-3} />
                <div className="w-10 h-10 bg-[#FA651E] text-white flex items-center justify-center group-hover:bg-[#E04803] transition-colors shrink-0">
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </div>
                <span className="px-4 py-2.5 text-xs sm:text-sm font-semibold tracking-tight text-white">
                  Schedule Enterprise Consultation →
                </span>
              </Link>

              {/* Feature Checklist */}
              <div className="border-t border-neutral-100 pt-8">
                <div className="text-xs font-mono uppercase tracking-wider text-neutral-400 font-bold mb-4">
                  Full Enterprise Suite
                </div>
                <ul className="space-y-3.5 text-xs sm:text-sm text-neutral-700">
                  {enterpriseFeatures.map((feat) => (
                    <li key={feat} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-[#FA651E] shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
