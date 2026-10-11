"use client";

import React, { useState } from "react";
import { CornerMarks } from "./CornerMarks";
import {
  Shield,
  ArrowRight,
  Search,
  AlertTriangle,
  Network,
  Activity,
  CheckCircle2,
  Lock,
  Star,
} from "lucide-react";

interface HeroSectionProps {
  onLaunchDemo: (domain: string) => void;
}

export function HeroSection({ onLaunchDemo }: HeroSectionProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a supplier name or domain (e.g. tsmc.com, basf.com)");
      return;
    }
    setError("");
    onLaunchDemo(url.trim());
  };

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden bg-[#FAF9F6]">
      {/* Background Ambience: Signature Warm Peach / Coral Radial Mesh */}
      <div
        className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[620px] opacity-70"
        style={{
          background:
            "radial-gradient(ellipse at 50% 15%, rgba(253, 138, 107, 0.28) 0%, rgba(250, 101, 30, 0.12) 35%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      {/* Decorative Subtle Flowing Lines from Left & Right */}
      <svg
        className="pointer-events-none absolute top-12 left-0 w-full h-[650px] opacity-40 -z-10"
        viewBox="0 0 1440 650"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <path
          d="M-50,80 C200,80 320,320 360,520"
          stroke="#FA651E"
          strokeWidth="1.2"
          strokeDasharray="4 4"
          opacity="0.35"
        />
        <path
          d="M-20,120 C180,140 280,360 360,520"
          stroke="#FD8A6B"
          strokeWidth="1.5"
          opacity="0.5"
        />
        <path
          d="M1490,80 C1240,80 1120,320 1080,520"
          stroke="#FA651E"
          strokeWidth="1.2"
          strokeDasharray="4 4"
          opacity="0.35"
        />
        <path
          d="M1460,120 C1260,140 1160,360 1080,520"
          stroke="#FD8A6B"
          strokeWidth="1.5"
          opacity="0.5"
        />
      </svg>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        {/* Status Badge with Corner Ticks */}
        <div className="inline-flex items-center justify-center mb-7">
          <div className="relative px-3.5 py-1.5 bg-white/80 backdrop-blur-sm border border-neutral-200/80 rounded text-xs font-mono tracking-tight text-neutral-800 shadow-[0_2px_8px_rgba(0,0,0,0.03)] flex items-center gap-2">
            <CornerMarks size={6} color="#d4d4d4" thickness={1} offset={-3} />
            <span className="w-2 h-2 rounded-full bg-[#FA651E] animate-pulse" />
            <span className="text-neutral-500">ENTERPRISE RISK INTELLIGENCE</span>
            <span className="text-neutral-300">|</span>
            <span className="text-[#FA651E] font-semibold">24/7 MULTI-TIER RADAR</span>
          </div>
        </div>

        {/* Hero Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-[68px] font-extrabold tracking-[-0.04em] text-[#0A0A0A] leading-[1.08] sm:leading-[1.06] mb-6">
          Predict supply chain shocks <br className="hidden sm:inline" />
          before physical shipments stall.
        </h1>

        {/* Hero Subheadline */}
        <p className="max-w-3xl mx-auto text-base sm:text-lg text-neutral-600 leading-relaxed font-normal mb-9">
          Provenance continuously monitors global sanctions, export bans, and trade restrictions.
          Our deterministic engine maps external events to your multi-tier supplier graph — calculating
          exact dollar exposure with cited evidence chains.
        </p>

        {/* Interactive Domain / Supplier Entity Scanner */}
        <div className="max-w-xl mx-auto mb-8 relative">
          <form
            onSubmit={handleSubmit}
            className="relative p-1.5 bg-white rounded-xl border border-neutral-200/90 shadow-[0_8px_30px_rgb(0,0,0,0.06)] flex flex-col sm:flex-row items-center gap-2"
          >
            <CornerMarks size={8} color="#a3a3a3" thickness={1.2} offset={-4} />

            <div className="flex-1 flex items-center w-full px-3.5 py-2">
              <Search className="w-4 h-4 text-neutral-400 mr-2.5 shrink-0" />
              <input
                type="text"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Enter supplier domain or name (e.g. tsmc.com, basf.com)"
                className="w-full bg-transparent text-sm sm:text-base text-neutral-900 placeholder-neutral-400 focus:outline-none"
                aria-label="Enter supplier name or domain"
              />
            </div>

            <button
              type="submit"
              className="w-full sm:w-auto px-6 py-3 bg-[#0A0A0A] hover:bg-neutral-800 text-white text-xs sm:text-sm font-semibold tracking-tight rounded-lg transition-all duration-200 flex items-center justify-center gap-2 shrink-0 group shadow-md"
            >
              <span>Scan Multi-Tier Risk</span>
              <ArrowRight className="w-4 h-4 text-[#FD8A6B] group-hover:translate-x-0.5 transition-transform" />
            </button>
          </form>

          {error && (
            <p className="text-xs text-rose-600 mt-2 font-medium text-left px-2">
              {error}
            </p>
          )}

          <div className="mt-2.5 flex items-center justify-center gap-3 text-[11px] font-mono text-neutral-500">
            <span>• GLEIF LEI Registry</span>
            <span>• OFAC &amp; BIS Real-Time Cross-Reference</span>
            <span>• 100% Deterministic Math</span>
          </div>
        </div>

        {/* Social Proof Row */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-10 text-xs sm:text-[13px] text-neutral-600 mb-14">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-full bg-[#FA651E]/10 text-[#FA651E] flex items-center justify-center font-bold text-[11px] border border-[#FA651E]/20">
              ✓
            </div>
            <span className="text-neutral-700 font-medium">
              &ldquo;Detected graphite export curbs 11 days before our primary Tier-1 broker.&rdquo;
            </span>
          </div>

          <div className="hidden sm:block w-px h-4 bg-neutral-300" />

          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#FA651E]" />
            <span className="font-semibold text-neutral-900">Zero Hallucinations Guarantee</span>
            <span className="text-neutral-500 font-mono">100% Cited Evidence</span>
          </div>
        </div>

        {/* Browser Chrome Preview (app.provenance.ai) */}
        <div className="relative max-w-5xl mx-auto rounded-xl border border-neutral-200 bg-white shadow-[0_20px_50px_rgba(0,0,0,0.08)] overflow-hidden text-left">
          <CornerMarks size={10} color="#a3a3a3" thickness={1.2} offset={-5} />

          {/* Browser Top Chrome */}
          <div className="h-11 bg-neutral-100/80 border-b border-neutral-200 px-4 flex items-center justify-between">
            {/* Window Dots */}
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-[#EF4444]" />
              <div className="w-3 h-3 rounded-full bg-[#F59E0B]" />
              <div className="w-3 h-3 rounded-full bg-[#10B981]" />
            </div>

            {/* URL Bar */}
            <div className="max-w-md w-full bg-white border border-neutral-200/90 rounded-md py-1 px-3 flex items-center justify-center gap-2 text-xs font-mono text-neutral-600 shadow-inner">
              <Lock className="w-3 h-3 text-[#10B981]" />
              <span>https://app.provenance.ai/radar</span>
              <span className="text-[10px] text-neutral-400">· tenant: aerospace_systems</span>
            </div>

            {/* Mode Indicator */}
            <div className="text-[11px] font-mono text-neutral-400">
              <span className="hidden sm:inline">v2.4</span>
            </div>
          </div>

          {/* App Dashboard Preview Content */}
          <div className="p-4 sm:p-6 bg-[#FAF9F6] grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left Column: Live Threat Radar Feed */}
            <div className="lg:col-span-7 bg-white p-4 sm:p-5 rounded-lg border border-neutral-200/80 shadow-sm">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-neutral-100">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-900">
                    Active Regulatory &amp; Disruption Signals
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-neutral-400">3 High-Impact Shocks</span>
              </div>

              <div className="space-y-3">
                {/* Threat Item 1 */}
                <div className="p-3.5 rounded-lg border border-rose-100 bg-rose-50/40 hover:border-rose-300 transition-all flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded bg-rose-100 text-rose-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-neutral-900 flex items-center gap-2">
                        <span>BIS Entity List Amendment</span>
                        <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px] font-mono font-semibold">
                          CRITICAL 94/100
                        </span>
                      </div>
                      <div className="text-[11px] text-neutral-600 mt-1 leading-snug">
                        Export curbs on Advanced Silicon Carbide Substrates.
                        Intersects Tier-2 supplier <span className="text-neutral-900 font-medium">Shenzhen Micro Ingot</span>.
                      </div>
                      <div className="text-[10px] font-mono text-neutral-500 mt-1.5 flex items-center gap-2">
                        <span className="text-emerald-700 font-semibold">✓ Federal Register Vol. 89</span>
                        <span>•</span>
                        <span>$4.85M Spend Exposed</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-[10px] font-mono text-neutral-400">4m ago</span>
                  </div>
                </div>

                {/* Threat Item 2 */}
                <div className="p-3.5 rounded-lg border border-amber-100 bg-amber-50/40 hover:border-amber-300 transition-all flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded bg-amber-100 text-amber-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                      <Activity className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-neutral-900 flex items-center gap-2">
                        <span>EU Critical Raw Materials Quota</span>
                        <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[10px] font-mono font-semibold">
                          HIGH 78/100
                        </span>
                      </div>
                      <div className="text-[11px] text-neutral-600 mt-1 leading-snug">
                        Import tariff quota triggered on synthetic graphite anodes.
                        Single-source dependency flagged.
                      </div>
                      <div className="text-[10px] font-mono text-neutral-500 mt-1.5 flex items-center gap-2">
                        <span className="text-emerald-700 font-semibold">✓ EU Official Journal L-2024</span>
                        <span>•</span>
                        <span>$2.10M Spend Exposed</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-[10px] font-mono text-neutral-400">18m ago</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Multi-Tier Graph & Exposure Arithmetic */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              {/* Exposure Calculation Box */}
              <div className="bg-white p-4 rounded-lg border border-neutral-200/80 shadow-sm">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-neutral-100">
                  <span className="text-xs font-mono font-semibold text-neutral-700 uppercase flex items-center gap-1.5">
                    <Network className="w-3.5 h-3.5 text-[#FA651E]" />
                    Multi-Tier Graph Intersection
                  </span>
                  <span className="text-[11px] font-mono text-[#FA651E] font-semibold">Depth: 3 Tiers</span>
                </div>

                <div className="space-y-2 font-mono text-[11px]">
                  <div className="flex items-center justify-between p-2 rounded bg-neutral-50 border border-neutral-100">
                    <span className="text-neutral-500">Your Enterprise</span>
                    <span className="text-neutral-900 font-medium">Aero Dynamics Corp</span>
                  </div>
                  <div className="flex items-center justify-center text-neutral-400 py-0.5">
                    ↓ Tier 1 (Direct Supplier · $12.4M Spend)
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-neutral-50 border border-neutral-100">
                    <span className="text-neutral-500">Tier 1 Partner</span>
                    <span className="text-neutral-900 font-medium">Apex Avionics AG</span>
                  </div>
                  <div className="flex items-center justify-center text-rose-500 py-0.5">
                    ↓ Tier 2 (Sub-Supplier · Single Source)
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-rose-50 border border-rose-200">
                    <span className="text-rose-700 font-bold">Choke-Point Node</span>
                    <span className="text-rose-900 font-bold">Shenzhen Micro Ingot</span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-neutral-100 flex items-center justify-between text-xs">
                  <span className="text-neutral-600">Calculated Dollar Exposure:</span>
                  <span className="font-mono font-bold text-rose-600 text-sm">$4,850,000</span>
                </div>
              </div>

              {/* Evidence Chain Verification Status */}
              <div className="bg-white p-3.5 rounded-lg border border-neutral-200/80 shadow-sm flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <div className="text-xs">
                    <span className="text-neutral-900 font-medium">Zero Hallucinations Guarantee</span>
                    <p className="text-[11px] text-neutral-500">
                      Deterministic recursive SQL + 100% cited evidence
                    </p>
                  </div>
                </div>
                <span className="text-[11px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  VERIFIED
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
