"use client";

import React, { useState } from "react";
import { CornerMarks } from "./CornerMarks";
import { ProvenanceLogo } from "./ProvenanceLogo";

export function VennSection() {
  const [activeCircle, setActiveCircle] = useState<string | null>(null);

  return (
    <section className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="relative max-w-4xl mb-16 p-4 sm:p-6 bg-white/40 rounded-xl border border-neutral-200/60">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E]" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              Consolidated Risk Intelligence
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A] leading-tight mb-4">
            One platform. Replaces your <span className="text-[#FA651E]">fragmented risk stack</span>.
          </h2>

          <p className="text-base sm:text-lg text-neutral-600 font-normal">
            Legacy procurement tools are blind to external shocks, news monitors have no internal context, and spreadsheets rot. Provenance connects them all deterministically.
          </p>
        </div>

        {/* 4-Circle Venn Diagram Container */}
        <div className="relative max-w-4xl mx-auto bg-white rounded-2xl border border-neutral-200 p-8 sm:p-14 shadow-sm">
          <CornerMarks size={12} color="#FA651E" thickness={1.5} offset={-6} />

          <div className="relative w-full aspect-square max-w-[580px] mx-auto flex items-center justify-center">
            {/* SVG Background Coordinate Grid */}
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none opacity-20"
              viewBox="0 0 500 500"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="250" cy="250" r="240" stroke="#000" strokeWidth="0.5" strokeDasharray="2 4" />
              <line x1="250" y1="0" x2="250" y2="500" stroke="#000" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="0" y1="250" x2="500" y2="250" stroke="#000" strokeWidth="0.5" strokeDasharray="3 3" />
            </svg>

            {/* Circle 1: Top-Left (Legacy ERP / S2P) */}
            <div
              onMouseEnter={() => setActiveCircle("erp")}
              onMouseLeave={() => setActiveCircle(null)}
              className={`absolute top-6 left-6 w-[270px] sm:w-[310px] h-[270px] sm:h-[310px] rounded-full border border-neutral-400/80 transition-all duration-300 flex flex-col items-center justify-center p-6 ${
                activeCircle === "erp" ? "bg-orange-500/10 border-[#FA651E] scale-102" : "bg-neutral-50/20"
              }`}
            >
              <div className="absolute top-10 left-8 text-left">
                <span className="text-sm sm:text-base font-bold text-[#FA651E] tracking-tight block">
                  Legacy ERP &amp; S2P
                </span>
                <span className="text-[10px] font-mono text-neutral-400">Internal data only</span>
                <div className="mt-2 space-y-1.5 text-xs text-neutral-700 font-semibold">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-900" />
                    <span>SAP Ariba</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-600" />
                    <span>Coupa</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Circle 2: Top-Right (External News Feeds) */}
            <div
              onMouseEnter={() => setActiveCircle("news")}
              onMouseLeave={() => setActiveCircle(null)}
              className={`absolute top-6 right-6 w-[270px] sm:w-[310px] h-[270px] sm:h-[310px] rounded-full border border-neutral-400/80 transition-all duration-300 flex flex-col items-center justify-center p-6 ${
                activeCircle === "news" ? "bg-orange-500/10 border-[#FA651E] scale-102" : "bg-neutral-50/20"
              }`}
            >
              <div className="absolute top-10 right-8 text-right">
                <span className="text-sm sm:text-base font-bold text-neutral-900 tracking-tight block">
                  Unlinked News Feeds
                </span>
                <span className="text-[10px] font-mono text-neutral-400">No BOM or spend context</span>
                <div className="mt-2 space-y-1.5 text-xs text-neutral-700 font-semibold flex flex-col items-end">
                  <div className="flex items-center gap-1.5">
                    <span>Google Alerts</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span>Kharon / World-Check</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-800" />
                  </div>
                </div>
              </div>
            </div>

            {/* Circle 3: Bottom-Left (Manual Spreadsheets) */}
            <div
              onMouseEnter={() => setActiveCircle("sheets")}
              onMouseLeave={() => setActiveCircle(null)}
              className={`absolute bottom-6 left-6 w-[270px] sm:w-[310px] h-[270px] sm:h-[310px] rounded-full border border-neutral-400/80 transition-all duration-300 flex flex-col items-center justify-center p-6 ${
                activeCircle === "sheets" ? "bg-orange-500/10 border-[#FA651E] scale-102" : "bg-neutral-50/20"
              }`}
            >
              <div className="absolute bottom-10 left-8 text-left">
                <span className="text-sm sm:text-base font-bold text-neutral-900 tracking-tight block">
                  Manual Spreadsheets
                </span>
                <span className="text-[10px] font-mono text-neutral-400">Stale, zero sub-tier view</span>
                <div className="mt-2 space-y-1.5 text-xs text-neutral-700 font-semibold">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-700" />
                    <span>Excel Supplier Lists</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    <span>Isolated BI Exports</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Circle 4: Bottom-Right (Generic AI Chatbots) */}
            <div
              onMouseEnter={() => setActiveCircle("ai")}
              onMouseLeave={() => setActiveCircle(null)}
              className={`absolute bottom-6 right-6 w-[270px] sm:w-[310px] h-[270px] sm:h-[310px] rounded-full border border-neutral-400/80 transition-all duration-300 flex flex-col items-center justify-center p-6 ${
                activeCircle === "ai" ? "bg-orange-500/10 border-[#FA651E] scale-102" : "bg-neutral-50/20"
              }`}
            >
              <div className="absolute bottom-10 right-8 text-right">
                <span className="text-sm sm:text-base font-bold text-[#FA651E] tracking-tight block">
                  Generic AI Chatbots
                </span>
                <span className="text-[10px] font-mono text-neutral-400">Hallucinated arithmetic</span>
                <div className="mt-2 space-y-1.5 text-xs text-neutral-700 font-semibold flex flex-col items-end">
                  <div className="flex items-center gap-1.5">
                    <span>Unbounded Copilots</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-600" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span>ChatGPT Wrappers</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  </div>
                </div>
              </div>
            </div>

            {/* Center Intersection: Provenance Core Nexus */}
            <div className="relative z-20 w-32 h-32 sm:w-36 sm:h-36 rounded-full bg-white border-2 border-[#FA651E] shadow-[0_0_35px_rgba(250,101,30,0.35)] flex flex-col items-center justify-center p-2 group hover:scale-105 transition-transform text-center">
              <CornerMarks size={6} color="#FA651E" thickness={1} offset={-2} />
              <ProvenanceLogo size="sm" inverted={false} />
              <span className="text-[9px] font-mono text-neutral-400 mt-1 uppercase tracking-widest font-bold">
                DETERMINISTIC NEXUS
              </span>
            </div>

            {/* Pipeline Callouts */}
            <div className="absolute top-1/4 -left-4 sm:left-0 px-2.5 py-1 bg-white border border-neutral-200 rounded-md text-[11px] font-mono font-semibold text-neutral-600 shadow-sm">
              GLEIF Level-2
            </div>
            <div className="absolute bottom-1/4 -left-4 sm:left-0 px-2.5 py-1 bg-white border border-neutral-200 rounded-md text-[11px] font-mono font-semibold text-neutral-600 shadow-sm">
              Recursive SQL
            </div>
            <div className="absolute bottom-1/4 -right-4 sm:right-0 px-2.5 py-1 bg-white border border-neutral-200 rounded-md text-[11px] font-mono font-semibold text-neutral-600 shadow-sm">
              Evidence Citations
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
