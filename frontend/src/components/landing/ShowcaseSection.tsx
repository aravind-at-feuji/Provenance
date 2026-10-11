"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { CornerMarks } from "./CornerMarks";
import {
  Network,
  Radio,
  Calculator,
  FileCheck2,
  ArrowRight,
  Database,
  ExternalLink,
  Terminal,
} from "lucide-react";

interface ShowcaseSectionProps {
  onLaunchDemo?: () => void;
}

export function ShowcaseSection({ onLaunchDemo }: ShowcaseSectionProps) {
  const [activeStage, setActiveStage] = useState(0);

  const stages = [
    {
      step: "1/4",
      title: "Maps your multi-tier supply network automatically",
      tag: "GRAPH TOPOLOGY",
      description:
        "Ingest supplier lists or ERP spend data. Provenance cascades GLEIF Level-2 entity resolution to identify parent corporations, sub-tier component makers, and single-source choke points.",
      icon: Network,
    },
    {
      step: "2/4",
      title: "Continuous 24/7 regulatory & sanctions radar",
      tag: "REAL-TIME RADAR",
      description:
        "Continuously scans Tier-1 official registers including OFAC SDN, BIS Entity Lists, EU Sanctions, and Federal Register notices. Unstructured regulatory notices are resolved to canonical entities in seconds.",
      icon: Radio,
    },
    {
      step: "3/4",
      title: "Deterministic impact & dollar exposure scoring",
      tag: "DETERMINISTIC MATH",
      description:
        "Calculates business exposure using exact weighted formulas: [Severity × Spend × Criticality × Lead-Time]. Recursive SQL traverses multi-tier dependencies in sub-100ms. Zero LLM hallucinations.",
      icon: Calculator,
    },
    {
      step: "4/4",
      title: "Cited evidence chains & conversational investigation",
      tag: "CITED AUDIT TRAIL",
      description:
        "Every alert links directly to official legal gazette citations, purchase order lines, and supplier contracts. Interrogate disruption paths conversationally with AI Investigation Agent 4.",
      icon: FileCheck2,
      hasCta: true,
    },
  ];

  // Auto-advance stages every 7 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStage((prev) => (prev + 1) % stages.length);
    }, 7000);
    return () => clearInterval(timer);
  }, [stages.length]);

  return (
    <section id="features" className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header with Corner Marks */}
        <div className="relative max-w-4xl mb-16 p-4 sm:p-6 bg-white/40 rounded-xl border border-neutral-200/60">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E] animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              End-to-End Risk Architecture
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-[-0.035em] text-[#0A0A0A] leading-tight mb-4">
            From external regulatory shock to <br className="hidden sm:inline" />
            <span className="text-[#FA651E]">internal dollar exposure</span> in minutes.
          </h2>

          <p className="text-base sm:text-lg text-neutral-600 max-w-2xl font-normal">
            A battle-tested 4-stage pipeline that bridges official global trade registers with your internal purchase orders and supplier topology.
          </p>
        </div>

        {/* 4-Stage Showcase Container */}
        <div className="relative bg-white rounded-2xl border border-neutral-200 shadow-[0_12px_40px_rgba(0,0,0,0.04)] overflow-hidden">
          <CornerMarks size={12} color="#FA651E" thickness={1.5} offset={-6} />

          {/* Top Stage Tabs Navigation */}
          <div className="grid grid-cols-2 md:grid-cols-4 border-b border-neutral-200 bg-neutral-50/70">
            {stages.map((stg, idx) => {
              const Icon = stg.icon;
              return (
                <button
                  key={stg.step}
                  onClick={() => setActiveStage(idx)}
                  className={`p-4 text-left border-r last:border-r-0 border-neutral-200 transition-all flex flex-col justify-between ${
                    activeStage === idx
                      ? "bg-white text-neutral-900 border-b-2 border-b-[#FA651E]"
                      : "text-neutral-500 hover:bg-white/60 hover:text-neutral-800"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                        activeStage === idx
                          ? "bg-[#FA651E]/15 text-[#FA651E]"
                          : "bg-neutral-200/70 text-neutral-600"
                      }`}
                    >
                      <Icon className="w-3 h-3" />
                      Stage {stg.step}
                    </span>
                    {activeStage === idx && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FA651E]" />
                    )}
                  </div>
                  <span className="text-xs sm:text-sm font-semibold tracking-tight line-clamp-1">
                    {stg.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Main Stage Display (Left Copy + Right Visual) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
            {/* Left Copy Panel */}
            <div className="lg:col-span-5 p-8 sm:p-12 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-neutral-200 bg-white">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FA651E]/10 text-[#FA651E] text-xs font-mono font-bold mb-6">
                  <span>⬡</span>
                  <span>{stages[activeStage].step}</span>
                  <span className="text-neutral-300">|</span>
                  <span>{stages[activeStage].tag}</span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#0A0A0A] leading-tight mb-4">
                  {stages[activeStage].title}
                </h3>

                <p className="text-base text-neutral-600 leading-relaxed font-normal">
                  {stages[activeStage].description}
                </p>
              </div>

              {/* Stage Contextual Badges / CTA */}
              <div className="pt-8">
                {activeStage === 0 && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-neutral-200 bg-neutral-50 text-xs font-mono text-neutral-700">
                    <Database className="w-3.5 h-3.5 text-[#FA651E]" />
                    <span>GLEIF LEI Level-2 Entity Resolution</span>
                  </div>
                )}

                {activeStage === 1 && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-xs font-mono text-emerald-800">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Official Registers Synchronized (OFAC, BIS, EU, UK)</span>
                  </div>
                )}

                {activeStage === 2 && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-orange-200 bg-orange-50 text-xs font-mono text-orange-900">
                    <Calculator className="w-3.5 h-3.5 text-[#FA651E]" />
                    <span>Deterministic Weighting · 0% Math Hallucination</span>
                  </div>
                )}

                {activeStage === 3 && (
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-[#0A0A0A] hover:bg-neutral-800 text-white text-xs sm:text-sm font-semibold transition-all shadow-md group"
                  >
                    <span>Launch Investigation Console</span>
                    <ArrowRight className="w-4 h-4 text-[#FD8A6B] group-hover:translate-x-1 transition-transform" />
                  </Link>
                )}
              </div>
            </div>

            {/* Right Visual Stage Panel */}
            <div className="lg:col-span-7 p-6 sm:p-10 bg-[#FAF9F6] flex items-center justify-center relative overflow-hidden">
              {/* STAGE 1 VISUAL: Multi-Tier Graph Topology */}
              {activeStage === 0 && (
                <div className="w-full max-w-lg space-y-3 font-mono text-xs animate-in fade-in duration-300">
                  <div className="p-3.5 rounded-lg bg-white border border-neutral-200/90 shadow-sm flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="w-2 h-2 rounded-full bg-[#FA651E]" />
                      <span className="text-neutral-900 font-bold">Your Organization</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-neutral-100 text-neutral-600 font-semibold">
                      TENANT ROOT
                    </span>
                  </div>

                  <div className="pl-6 border-l-2 border-dashed border-orange-300 space-y-3">
                    <div className="p-3 rounded-lg bg-white border border-neutral-200/80 shadow-sm flex items-center justify-between">
                      <div>
                        <div className="text-neutral-900 font-semibold">Tier-1: Apex Avionics AG</div>
                        <div className="text-[10px] text-neutral-500">LEI: 529900T8BM49AURSDO55 · $14.2M Annual Spend</div>
                      </div>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                        VERIFIED
                      </span>
                    </div>

                    <div className="pl-6 border-l-2 border-dashed border-rose-300 space-y-2">
                      <div className="p-3 rounded-lg bg-rose-50/70 border border-rose-200 shadow-sm flex items-center justify-between">
                        <div>
                          <div className="text-rose-900 font-semibold">Tier-2: Shenzhen Micro Ingot</div>
                          <div className="text-[10px] text-rose-700">Sub-Tier Foundry · Silicon Carbide Substrates</div>
                        </div>
                        <span className="text-[10px] text-rose-700 bg-rose-100 px-2 py-0.5 rounded font-bold border border-rose-200">
                          CHOKEPOINT
                        </span>
                      </div>

                      <div className="pl-6 border-l-2 border-dashed border-rose-200">
                        <div className="p-2.5 rounded bg-white border border-neutral-200 text-[10px] text-neutral-600 flex items-center justify-between">
                          <span>Tier-3: Baotou Rare Earth Mining Corp</span>
                          <span className="text-amber-700 font-semibold">Raw Mineral Ingot</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STAGE 2 VISUAL: Continuous Regulatory Radar */}
              {activeStage === 1 && (
                <div className="w-full max-w-lg space-y-3 animate-in fade-in duration-300 font-mono text-xs">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-white border border-neutral-200/90 shadow-sm">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      <span className="text-neutral-900 font-bold">Regulatory Stream</span>
                    </div>
                    <span className="text-[11px] text-neutral-500">Polling Interval: 60s</span>
                  </div>

                  <div className="space-y-2.5">
                    <div className="p-3 rounded-lg bg-white border border-neutral-200/80 shadow-xs flex items-center justify-between">
                      <div>
                        <div className="text-neutral-900 font-medium flex items-center gap-2">
                          <span className="text-rose-600 font-bold">OFAC SDN List</span>
                          <span className="text-[10px] text-neutral-400">· US Treasury</span>
                        </div>
                        <div className="text-[11px] text-neutral-600 mt-0.5">
                          Added 14 entities under Executive Order 14024
                        </div>
                      </div>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                        INGESTED
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-neutral-200/80 shadow-xs flex items-center justify-between">
                      <div>
                        <div className="text-neutral-900 font-medium flex items-center gap-2">
                          <span className="text-amber-600 font-bold">Federal Register Vol. 89</span>
                          <span className="text-[10px] text-neutral-400">· BIS Rule Change</span>
                        </div>
                        <div className="text-[11px] text-neutral-600 mt-0.5">
                          Advanced Computing Export Controls 15 CFR § 744
                        </div>
                      </div>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                        RESOLVED
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-neutral-200/80 shadow-xs flex items-center justify-between">
                      <div>
                        <div className="text-neutral-900 font-medium flex items-center gap-2">
                          <span className="text-[#FA651E] font-bold">EU Sanctions Map</span>
                          <span className="text-[10px] text-neutral-400">· Council Reg 833/2014</span>
                        </div>
                        <div className="text-[11px] text-neutral-600 mt-0.5">
                          Dual-use technological item export restrictions
                        </div>
                      </div>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                        MATCHED
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* STAGE 3 VISUAL: Deterministic Exposure Arithmetic */}
              {activeStage === 2 && (
                <div className="w-full max-w-lg p-5 rounded-xl bg-white border border-neutral-200/90 shadow-md font-mono text-xs space-y-4 animate-in fade-in duration-300">
                  <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
                    <span className="text-neutral-800 uppercase tracking-wider font-bold">
                      Deterministic Impact Scoring Formula
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-orange-50 text-[#FA651E] font-semibold border border-orange-200">
                      v1.4 Weighted Model
                    </span>
                  </div>

                  <div className="bg-neutral-50 p-3 rounded border border-neutral-200/60 space-y-2">
                    <div className="text-[11px] text-neutral-600">
                      Score = (Severity × 0.35) + (SpendTier × 0.30) + (SingleSource × 0.20) + (LeadTime × 0.15)
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[10px] pt-1">
                      <div className="text-neutral-700">• Event Severity: 0.95 (OFAC SDN)</div>
                      <div className="text-neutral-700">• Annual Spend: $4.85M (Tier High)</div>
                      <div className="text-neutral-700">• Single Source: 1.0 (True)</div>
                      <div className="text-neutral-700">• Lead Time: 90 Days</div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded bg-rose-50 border border-rose-200 flex items-center justify-between">
                    <div>
                      <div className="text-xs text-rose-800 font-bold uppercase">Computed Composite Risk</div>
                      <div className="text-[11px] text-neutral-500">Action: Immediate Incident Alert</div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-black text-rose-600">92 / 100</div>
                      <span className="text-[9px] text-rose-700 uppercase font-bold tracking-wider">
                        CRITICAL SEVERITY
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* STAGE 4 VISUAL: Cited Evidence Dossier & Agent 4 */}
              {activeStage === 3 && (
                <div className="w-full max-w-lg space-y-3 font-mono text-xs animate-in fade-in duration-300">
                  <div className="p-3.5 rounded-lg bg-white border border-neutral-200/90 shadow-sm">
                    <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100">
                      <span className="text-neutral-900 font-bold flex items-center gap-2">
                        <Terminal className="w-3.5 h-3.5 text-[#FA651E]" />
                        AI Investigation Agent (Agent 4)
                      </span>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                        GROUNDED RAG
                      </span>
                    </div>
                    <p className="text-[11px] text-neutral-700 font-sans leading-relaxed">
                      &ldquo;Tier-2 supplier <strong className="text-neutral-900">Shenzhen Micro Ingot</strong> is subject to Commerce Dept export controls published in Federal Register Vol. 89 No. 42. Impact: Halts silicon substrate delivery for Apex Avionics PO-49219 ($4.85M).&rdquo;
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="p-2.5 rounded bg-white border border-neutral-200/80 shadow-xs flex items-center justify-between text-[11px]">
                      <span className="text-neutral-600">Citation [1]: Federal Register Document #2024-04912</span>
                      <span className="text-[#FA651E] font-semibold flex items-center gap-1">
                        Live Gazette <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>

                    <div className="p-2.5 rounded bg-white border border-neutral-200/80 shadow-xs flex items-center justify-between text-[11px]">
                      <span className="text-neutral-600">Citation [2]: Contract Term Schedule Exhibit C</span>
                      <span className="text-[#FA651E] font-semibold flex items-center gap-1">
                        SAP PO #49219 <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
