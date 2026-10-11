"use client";

import React, { useState } from "react";
import { CornerMarks } from "./CornerMarks";
import {
  UploadCloud,
  Network,
  ShieldAlert,
  FileSpreadsheet,
} from "lucide-react";

export function SetupWalkthroughSection() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      tab: "1. Ingest & Resolve",
      num: "01",
      badge: "ZERO COLD-START",
      title: "Upload your supplier base or sync your ERP",
      description:
        "Upload a simple CSV supplier list, drop in purchase order exports, or connect your ERP. Provenance deduplicates vendors and resolves canonical entities against global GLEIF LEI registries.",
      subtext: "No manual taxonomy building required.",
      icon: UploadCloud,
    },
    {
      tab: "2. Map Multi-Tier",
      num: "02",
      badge: "AUTOMATIC DISCOVERY",
      title: "GLEIF Level-2 builds your multi-tier hierarchy",
      description:
        "Provenance automatically traverses parent-subsidiary relationships and sub-tier component suppliers, illuminating hidden single-source choke points across Tier 1, 2, and 3.",
      subtext: "Reveals sub-tier dependencies before disruptions strike.",
      icon: Network,
    },
    {
      tab: "3. 30-Day Backfill",
      num: "03",
      badge: "DAY-ONE VALUE",
      title: "First cited alerts appear in under 5 minutes",
      description:
        "Our ingestion pipeline immediately executes a 30-day retroactive sweep over all official sanctions, export controls, and regulatory notices to deliver immediate, verifiable findings.",
      subtext: "Guaranteed immediate visibility into live external exposure.",
      icon: ShieldAlert,
    },
  ];

  return (
    <section id="how-it-works" className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="relative max-w-4xl mb-16 p-4 sm:p-6 bg-white/40 rounded-xl border border-neutral-200/60">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E]" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              Rapid Time to Value
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A] leading-tight mb-4">
            <span className="text-[#FA651E]">15 minutes</span> from CSV upload to active disruption defense.
          </h2>

          <p className="text-base sm:text-lg text-neutral-600 font-normal">
            No 6-month consulting integration. Connect your vendor roster and let our deterministic pipeline resolve your multi-tier risk immediately.
          </p>
        </div>

        {/* 3-Step Interactive Container */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center bg-white rounded-2xl border border-neutral-200 p-8 sm:p-12 shadow-sm relative">
          <CornerMarks size={12} color="#FA651E" thickness={1.5} offset={-6} />

          {/* Left: Step Tab Selectors */}
          <div className="md:col-span-5 space-y-4">
            {steps.map((st, index) => {
              const Icon = st.icon;
              const isActive = activeStep === index;
              return (
                <button
                  key={st.tab}
                  onClick={() => setActiveStep(index)}
                  className={`w-full text-left p-4 sm:p-5 rounded-xl border transition-all flex items-center justify-between group ${
                    isActive
                      ? "bg-orange-50/60 border-[#FA651E] shadow-sm text-neutral-900"
                      : "bg-neutral-50/50 border-neutral-200/70 text-neutral-500 hover:bg-neutral-100/60 hover:text-neutral-900"
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center font-mono font-bold text-xs ${
                        isActive
                          ? "bg-[#FA651E] text-white shadow-xs"
                          : "bg-neutral-200 text-neutral-600 group-hover:bg-neutral-300"
                      }`}
                    >
                      {st.num}
                    </div>
                    <div>
                      <span className="text-sm sm:text-base font-semibold tracking-tight block">
                        {st.tab}
                      </span>
                      <span className="text-[11px] font-mono text-neutral-400 group-hover:text-neutral-500">
                        {st.badge}
                      </span>
                    </div>
                  </div>
                  <Icon
                    className={`w-5 h-5 ${
                      isActive ? "text-[#FA651E]" : "text-neutral-400 group-hover:text-neutral-600"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          {/* Right: Step Detail Visual Stage */}
          <div className="md:col-span-7 bg-[#FAF9F6] rounded-xl border border-neutral-200/80 p-6 sm:p-8 flex flex-col justify-between min-h-[400px]">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FA651E]/10 border border-[#FA651E]/20 text-[#FA651E] text-xs font-mono font-bold mb-4">
                <span>STEP {steps[activeStep].num}</span>
                <span className="text-neutral-300">|</span>
                <span>{steps[activeStep].badge}</span>
              </div>

              <h3 className="text-xl sm:text-2xl font-bold text-[#0A0A0A] mb-3">
                {steps[activeStep].title}
              </h3>

              <p className="text-sm sm:text-base text-neutral-600 leading-relaxed mb-6">
                {steps[activeStep].description}
              </p>
            </div>

            {/* Custom Interactive Mockup Visuals per Step */}
            <div className="pt-4 border-t border-neutral-200">
              {activeStep === 0 && (
                <div className="p-4 rounded-lg bg-white border border-neutral-200/80 shadow-xs font-mono text-xs space-y-2.5">
                  <div className="flex items-center justify-between text-neutral-600 pb-2 border-b border-neutral-100">
                    <span className="flex items-center gap-1.5 text-neutral-900 font-semibold">
                      <FileSpreadsheet className="w-3.5 h-3.5 text-[#FA651E]" />
                      suppliers_2024_q3.csv (412 records)
                    </span>
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      100% PARSED
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>GLEIF LEI Match Rate:</span>
                    <span className="text-emerald-700 font-bold">96.8% Auto-Resolved</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Entities Sent to Review Queue:</span>
                    <span className="text-amber-700 font-bold">13 records (3.2%)</span>
                  </div>
                </div>
              )}

              {activeStep === 1 && (
                <div className="p-4 rounded-lg bg-white border border-neutral-200/80 shadow-xs font-mono text-xs space-y-2">
                  <div className="text-neutral-700 pb-1.5 border-b border-neutral-100 flex items-center justify-between font-semibold">
                    <span>Multi-Tier Tree Generation</span>
                    <span className="text-[#FA651E]">Level-2 GLEIF Enrichment</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Tier 1 Direct Suppliers:</span>
                    <span className="text-neutral-900 font-bold">412 nodes</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Discovered Sub-Tier Partners:</span>
                    <span className="text-[#FA651E] font-bold">1,840 nodes (Tiers 2 &amp; 3)</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-rose-700">
                    <span>Identified Single-Source Bottlenecks:</span>
                    <span className="text-rose-700 font-bold">19 critical choke points</span>
                  </div>
                </div>
              )}

              {activeStep === 2 && (
                <div className="p-4 rounded-lg bg-white border border-rose-200 shadow-xs font-mono text-xs space-y-2">
                  <div className="text-neutral-900 pb-1.5 border-b border-neutral-100 flex items-center justify-between">
                    <span className="text-rose-700 font-bold flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                      30-Day Historical Backfill Complete
                    </span>
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      5 mins elapsed
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Total Regulatory Events Scanned:</span>
                    <span className="text-neutral-900 font-bold">14,290 notices</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Graph Intersections Detected:</span>
                    <span className="text-amber-700 font-bold">4 active alerts generated</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-600">
                    <span>Immediate Exposed Dollar Value:</span>
                    <span className="text-rose-700 font-bold">$7,420,000</span>
                  </div>
                </div>
              )}

              <p className="text-xs text-neutral-500 font-mono mt-3.5">
                ✓ {steps[activeStep].subtext}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
