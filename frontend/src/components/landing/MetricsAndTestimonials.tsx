"use client";

import React from "react";
import { CornerMarks } from "./CornerMarks";
import { ShieldCheck, Quote } from "lucide-react";

export function MetricsAndTestimonials() {
  const metrics = [
    {
      value: "100%",
      sub: "Deterministic & auditable risk calculations",
    },
    {
      value: "< 5 Mins",
      sub: "From official gazette publication to exposure alert",
    },
    {
      value: "$14.8M",
      sub: "Average disruption spend protected per 1,000 suppliers",
    },
  ];

  const testimonials = [
    {
      name: "Marcus Vance",
      role: "Global Head of Supply Chain Risk",
      company: "Aerospace Systems Corp",
      initials: "MV",
      badgeColor: "bg-blue-100 text-blue-800",
      quote:
        "Provenance detected the Chinese graphite export restrictions 11 days before our primary Tier-1 broker sent an alert. We pre-qualified an alternate Korean supplier before market prices surged 40%.",
    },
    {
      name: "Elena Rostova",
      role: "VP of Strategic Direct Procurement",
      company: "Global Automotive Electrics",
      initials: "ER",
      badgeColor: "bg-orange-100 text-[#9A3412]",
      quote:
        "The multi-tier graph revealed that 4 of our Tier-1 wiring harness vendors were relying on the same sanctioned copper smelter in Central Asia. We eliminated a catastrophic single-point-of-failure in one afternoon.",
    },
    {
      name: "David Chen",
      role: "Chief Compliance & Trade Officer",
      company: "Industrial Robotics Group",
      initials: "DC",
      badgeColor: "bg-emerald-100 text-emerald-800",
      quote:
        "Every alert comes with the exact Federal Register volume and contract purchase order citation. Zero hallucinated AI summaries. Our general counsel accepts Provenance reports directly for export filings.",
    },
    {
      name: "Sarah Al-Mansoor",
      role: "Category Director, Critical Minerals",
      company: "Renewable Energy Grid Solutions",
      initials: "SA",
      badgeColor: "bg-purple-100 text-purple-800",
      quote:
        "The spend leakage detection with regulatory overlap is extraordinary. It flagged an uncontracted price spike right when the sub-supplier was placed under EU dual-use review. Saved us over $2.1M.",
    },
  ];

  return (
    <section id="case-studies" className="py-24 bg-[#FAF9F6] border-b border-neutral-200/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Headline with Registration Frame */}
        <div className="relative max-w-4xl mb-16 p-6 sm:p-8 bg-white/40 rounded-xl border border-neutral-200/60">
          <CornerMarks size={8} color="#c7c7c7" thickness={1} offset={-4} />

          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FA651E]" />
            <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 font-semibold">
              Enterprise Impact
            </span>
          </div>

          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0A0A0A] leading-[1.12]">
            Risk leaders stopped discovering disruptions from late shipments.{" "}
            <span className="text-[#FA651E]">Provenance alerts them first</span>.
          </h2>
        </div>

        {/* 3 Metric Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20 text-center">
          {metrics.map((m) => (
            <div
              key={m.value}
              className="relative p-8 bg-white rounded-xl border border-neutral-200 shadow-sm flex flex-col items-center justify-center hover:border-orange-200 transition-all"
            >
              <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />
              <div className="text-5xl sm:text-6xl font-extrabold tracking-tight text-[#0A0A0A] mb-3">
                {m.value}
              </div>
              <p className="text-sm sm:text-base text-neutral-600 font-medium max-w-xs">
                {m.sub}
              </p>
            </div>
          ))}
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="relative bg-white rounded-xl border border-neutral-200 p-6 shadow-sm flex flex-col justify-between hover:shadow-md hover:border-orange-200 transition-all group"
            >
              <CornerMarks size={8} color="#d4d4d4" thickness={1} offset={-4} />

              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-11 h-11 rounded-full flex items-center justify-center font-bold text-sm tracking-tight shrink-0 border border-neutral-200 ${t.badgeColor}`}
                  >
                    {t.initials}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-neutral-900 leading-tight">
                      {t.name}
                    </h4>
                    <p className="text-xs text-neutral-500 line-clamp-1">{t.role}</p>
                    <p className="text-[10px] font-mono text-[#FA651E]">{t.company}</p>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-neutral-600 leading-relaxed italic">
                  &ldquo;{t.quote}&rdquo;
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-neutral-100 flex items-center justify-between text-[11px] font-mono text-neutral-400">
                <span className="flex items-center gap-1 text-emerald-700">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Verified Customer
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
