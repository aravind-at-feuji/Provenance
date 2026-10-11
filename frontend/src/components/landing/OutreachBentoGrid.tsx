"use client";

import React, { useState } from "react";
import { CornerMarks } from "./CornerMarks";
import {
  Network,
  FileSpreadsheet,
  Terminal,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  Scale,
} from "lucide-react";

export function OutreachBentoGrid() {
  const [highAlertMode, setHighAlertMode] = useState(false);

  return (
    <section className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="relative max-w-4xl mb-16 p-4 sm:p-6 bg-white/40 rounded-xl border border-neutral-200/60">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E]" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              Mission-Critical Capabilities
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#0A0A0A] leading-tight mb-4">
            Engineered for <span className="text-[#FA651E]">zero hallucinations</span>.
          </h2>

          <p className="text-base sm:text-lg text-neutral-600 font-normal">
            Where other AI platforms hallucinate risk scores and fabricate supplier linkages, Provenance separates deterministic computation from generative synthesis.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: MULTI-TIER GRAPH */}
          <div className="relative bg-white rounded-xl border border-neutral-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all group">
            <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />
            <div>
              <div className="inline-flex items-center gap-2 mb-4 text-xs font-mono font-bold tracking-wider text-neutral-400 uppercase">
                <Network className="w-3.5 h-3.5 text-[#FA651E]" />
                <span>TOPOLOGY</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] mb-3">
                Recursive Multi-Tier Graph Traversal
              </h3>
              <p className="text-sm text-neutral-600 leading-relaxed">
                Traverses up to 5 tiers deep in sub-100ms via recursive SQL CTEs. Uncovers hidden concentration nodes where multiple Tier-1 suppliers source from the same sanctioned smelter or sub-foundry.
              </p>
            </div>

            <div className="mt-8 p-3 rounded-lg bg-neutral-50 border border-neutral-100 flex items-center justify-between text-xs font-mono text-neutral-600">
              <span>Depth Traversal: Tier 1 → 5</span>
              <span className="text-emerald-700 font-bold">&lt; 100ms</span>
            </div>
          </div>

          {/* Card 2: DETERMINISTIC VS AI (Large middle card) */}
          <div className="relative bg-white rounded-xl border border-neutral-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all group md:col-span-2">
            <CornerMarks size={8} color="#FA651E" thickness={1.2} offset={-4} />
            <div>
              <div className="inline-flex items-center gap-2 mb-4 text-xs font-mono font-bold tracking-wider text-neutral-400 uppercase">
                <Scale className="w-3.5 h-3.5 text-[#FA651E]" />
                <span>ARCHITECTURAL SEPARATION</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] mb-3">
                Deterministic Arithmetic vs. AI Natural Language
              </h3>
              <p className="text-sm text-neutral-600 leading-relaxed max-w-xl">
                The default is deterministic. An LLM is strictly used for unstructured legal gazette extraction and natural language explanations. Risk scores, dollar exposure sums, and thresholds are computed by auditable Python formulas and PostgreSQL.
              </p>
            </div>

            {/* Architectural Badges in Reference Warm Palette */}
            <div className="mt-8 flex flex-wrap items-center gap-2.5">
              <span className="px-3 py-1.5 rounded-full bg-[#FEF08A] text-[#854D0E] text-xs font-semibold shadow-xs">
                Exact Math Scoring
              </span>
              <span className="px-3 py-1.5 rounded-full bg-[#FD8A6B]/25 text-[#9A3412] text-xs font-semibold shadow-xs">
                Zero Math Hallucination
              </span>
              <span className="px-3 py-1.5 rounded-full bg-[#A7F3D0] text-[#065F46] text-xs font-semibold shadow-xs">
                Grounded RAG Explanations
              </span>
              <span className="px-3 py-1.5 rounded-full bg-[#FDE047]/60 text-[#713F12] text-xs font-semibold shadow-xs">
                Auditable Across Reviews
              </span>
            </div>
          </div>

          {/* Card 3: SPEND LEAKAGE */}
          <div className="relative bg-white rounded-xl border border-neutral-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all group">
            <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />
            <div>
              <div className="inline-flex items-center gap-2 mb-4 text-xs font-mono font-bold tracking-wider text-neutral-400 uppercase">
                <FileSpreadsheet className="w-3.5 h-3.5 text-[#FA651E]" />
                <span>SPEND INTELLIGENCE</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] mb-3">
                Spend Leakage &amp; Regulatory Overlap
              </h3>
              <p className="text-sm text-neutral-600 leading-relaxed">
                Flags duplicate invoices, contract price variances, and uncontracted tail spend. Cross-checks findings against open geopolitical risks with compound flags (<code className="text-[#FA651E] font-mono">regulatory_overlap = true</code>).
              </p>
            </div>

            <div className="mt-8 p-3 rounded-lg bg-neutral-50 border border-neutral-100 flex items-center justify-between text-xs font-mono text-neutral-600">
              <span>Contract Variance Detection</span>
              <span className="text-[#FA651E] font-bold">Automated</span>
            </div>
          </div>

          {/* Card 4: INTERACTIVE ALERT MODE TOGGLE */}
          <div className="relative bg-white rounded-xl border border-neutral-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all group">
            <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />
            <div>
              <div className="inline-flex items-center gap-2 mb-4 text-xs font-mono font-bold tracking-wider text-neutral-400 uppercase">
                <ShieldCheck className="w-3.5 h-3.5 text-[#FA651E]" />
                <span>ALERT SENSITIVITY</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] mb-3">
                Digest-First vs. Instant Push
              </h3>
              <p className="text-sm text-neutral-600 leading-relaxed">
                Prevents alert fatigue with smart weekly digest batching, while reserving instant multi-channel push alerts for critical geopolitical shocks.
              </p>
            </div>

            {/* Interactive Toggle */}
            <div className="mt-8 p-4 rounded-lg bg-neutral-50 border border-neutral-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-neutral-900 block">
                  {highAlertMode ? "DEFCON-1 IMMEDIATE PUSH" : "DIGEST-FIRST FILTER"}
                </span>
                <span className="text-[10px] text-neutral-500">
                  {highAlertMode ? "Instant SMS & Slack on ≥ HIGH severity" : "Filtered weekly summary batches"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setHighAlertMode(!highAlertMode)}
                className="text-neutral-400 hover:text-neutral-900 focus:outline-none"
                aria-label="Toggle alert sensitivity mode"
              >
                {highAlertMode ? (
                  <ToggleRight className="w-8 h-8 text-[#FA651E]" />
                ) : (
                  <ToggleLeft className="w-8 h-8 text-neutral-400" />
                )}
              </button>
            </div>
          </div>

          {/* Card 5: AI CONVERSATIONAL INVESTIGATION */}
          <div className="relative bg-white rounded-xl border border-neutral-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between hover:border-orange-200 transition-all group">
            <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />
            <div>
              <div className="inline-flex items-center gap-2 mb-4 text-xs font-mono font-bold tracking-wider text-neutral-400 uppercase">
                <Terminal className="w-3.5 h-3.5 text-[#FA651E]" />
                <span>INVESTIGATION AGENT</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] mb-3">
                Agent 4: Multi-Tier Interrogation
              </h3>
              <p className="text-sm text-neutral-600 leading-relaxed">
                Ask &ldquo;Why was this supplier flagged?&rdquo; and receive an authoritative response linking the specific regulation to your purchase order numbers and parts.
              </p>
            </div>

            <div className="mt-8 p-3 rounded-lg bg-neutral-50 border border-neutral-100 flex items-center justify-between text-xs font-mono text-neutral-600">
              <span className="text-neutral-600">&ldquo;Explain our gallium exposure&rdquo;</span>
              <span className="text-[#FA651E] font-bold">Cited</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
