"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ProvenanceLogo } from "./ProvenanceLogo";
import { CornerMarks } from "./CornerMarks";
import { ArrowRight, Menu, X } from "lucide-react";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Multi-Tier Graph", sup: "01", href: "#features" },
    { label: "Regulatory Radar", sup: "02", href: "#radar" },
    { label: "Deterministic Engine", sup: "03", href: "#engine" },
    { label: "Integrations", sup: "04", href: "#integrations" },
    { label: "Platform Plans", sup: "05", href: "#pricing" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        isScrolled
          ? "bg-[#FAF9F6]/85 backdrop-blur-md border-b border-black/[0.06] shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)]"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[68px] flex items-center justify-between">
        {/* Left: Provenance Official Logo */}
        <div className="flex items-center">
          <Link href="/" className="group flex items-center gap-3">
            <ProvenanceLogo size="md" inverted={false} withTagline={true} />
          </Link>
        </div>

        {/* Center: Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-7 text-[13.5px] font-medium text-neutral-600">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="group inline-flex items-center gap-1 hover:text-neutral-950 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#FA651E] rounded py-1 px-1.5"
            >
              <span>{link.label}</span>
              <sup className="text-[10px] font-mono text-neutral-400 group-hover:text-[#FA651E] transition-colors">
                {link.sup}
              </sup>
            </Link>
          ))}
        </nav>

        {/* Right: Actions */}
        <div className="hidden sm:flex items-center gap-3">
          {/* Sign In Button with Corner Marks */}
          <Link
            href="/sign-in"
            className="relative group px-4 py-2 text-[13px] font-medium text-neutral-800 hover:text-neutral-950 transition-colors"
          >
            <CornerMarks size={6} color="#d4d4d4" thickness={1} offset={-2} />
            <span className="relative z-10">Client Portal</span>
          </Link>

          {/* Launch Live Radar CTA */}
          <Link
            href="/dashboard"
            className="relative group inline-flex items-center bg-white hover:bg-neutral-50 text-neutral-900 border border-neutral-200/80 rounded-sm shadow-sm transition-all duration-200"
          >
            <CornerMarks size={7} color="#a3a3a3" thickness={1.2} offset={-3} />

            {/* Coral/Orange square with arrow */}
            <div className="w-8 h-8 bg-[#FA651E] text-white flex items-center justify-center group-hover:bg-[#E04803] transition-colors">
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>

            {/* Label */}
            <span className="px-3.5 py-1.5 text-[13px] font-semibold tracking-tight">
              Launch Live Radar
            </span>
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex sm:hidden items-center">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-neutral-700 hover:text-neutral-950 focus:outline-none focus:ring-2 focus:ring-[#FA651E] rounded-md"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden bg-[#FAF9F6] border-b border-neutral-200/80 px-4 pt-3 pb-6 shadow-xl animate-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-between py-2.5 text-sm font-medium text-neutral-700 hover:text-neutral-950 border-b border-neutral-100"
              >
                <span>{link.label}</span>
                <span className="text-xs font-mono text-[#FA651E]">{link.sup}</span>
              </Link>
            ))}

            <div className="pt-3 flex flex-col gap-2">
              <Link
                href="/sign-in"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center py-2.5 text-sm font-medium border border-neutral-200 rounded-md text-neutral-800 hover:bg-neutral-50"
              >
                Client Portal
              </Link>
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-semibold bg-[#FA651E] text-white rounded-md hover:bg-[#E04803]"
              >
                <span>Launch Live Radar</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
