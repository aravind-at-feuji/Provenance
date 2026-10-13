import React from "react";
import Link from "next/link";
import { ProvenanceLogo } from "./ProvenanceLogo";

export function Footer() {
  return (
    <footer className="bg-[#FAF9F6] border-t border-neutral-200/80 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-16 border-b border-neutral-200/60">
          {/* Brand Info */}
          <div className="md:col-span-5 space-y-4">
            <ProvenanceLogo size="lg" inverted={false} withTagline={true} />
            <p className="text-sm text-neutral-600 font-medium max-w-sm">
              Autonomous multi-tier supply chain risk intelligence. Monitor global trade and regulatory shocks before physical shipments stall.
            </p>
          </div>

          {/* Column 1: Platform */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-900 font-bold">
              Platform
            </h4>
            <ul className="space-y-2 text-sm text-neutral-600">
              <li>
                <Link href="/graph" className="hover:text-neutral-950 transition-colors">
                  Multi-Tier Graph
                </Link>
              </li>
              <li>
                <Link href="/alerts" className="hover:text-neutral-950 transition-colors">
                  Risk Alerts
                </Link>
              </li>
              <li>
                <Link href="/investigate" className="hover:text-neutral-950 transition-colors">
                  AI Investigation
                </Link>
              </li>
              <li>
                <Link href="/suppliers" className="hover:text-neutral-950 transition-colors">
                  Supply Chain Network
                </Link>
              </li>
              <li>
                <Link href="/material-requests" className="hover:text-neutral-950 transition-colors">
                  Material Requests
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Ingestion Sources */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-900 font-bold">
              Official Registers
            </h4>
            <ul className="space-y-2 text-sm text-neutral-600">
              <li>
                <span className="text-neutral-700">OFAC SDN List</span>
              </li>
              <li>
                <span className="text-neutral-700">BIS Entity List</span>
              </li>
              <li>
                <span className="text-neutral-700">EU Sanctions Map</span>
              </li>
              <li>
                <span className="text-neutral-700">Federal Register</span>
              </li>
              <li>
                <span className="text-neutral-700">GLEIF LEI Master</span>
              </li>
            </ul>
          </div>

          {/* Column 3: Portals & Compliance */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-900 font-bold">
              Enterprise Access
            </h4>
            <ul className="space-y-2 text-sm text-neutral-600">
              <li>
                <Link href="/dashboard" className="hover:text-neutral-950 transition-colors font-medium text-[#FA651E]">
                  Open Live Dashboard →
                </Link>
              </li>
              <li>
                <Link href="/sign-in" className="hover:text-neutral-950 transition-colors">
                  Client Portal Login
                </Link>
              </li>
              <li>
                <span className="text-neutral-700">Deterministic Engine v1.4</span>
              </li>
              <li>
                <span className="text-neutral-700">SOC2 Type II &amp; Tenant RLS</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-neutral-500">
          <div>
            © {new Date().getFullYear()} Provenance Technologies, Inc. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="hover:text-neutral-900 transition-colors">
              App Terminal
            </Link>
            <span className="text-neutral-300">|</span>
            <span className="text-neutral-500">Multi-Tier Supply Chain Risk Intelligence</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
