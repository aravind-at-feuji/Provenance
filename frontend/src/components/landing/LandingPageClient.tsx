"use client";

import React, { useState } from "react";
import { Navbar } from "./Navbar";
import { HeroSection } from "./HeroSection";
import { TrustBar } from "./TrustBar";
import { ShowcaseSection } from "./ShowcaseSection";
import { SetupWalkthroughSection } from "./SetupWalkthroughSection";
import { OutreachBentoGrid } from "./OutreachBentoGrid";
import { VennSection } from "./VennSection";
import { MetricsAndTestimonials } from "./MetricsAndTestimonials";
import { IntegrationsSection } from "./IntegrationsSection";
import { PricingSection } from "./PricingSection";
import { FinalCTASection } from "./FinalCTASection";
import { Footer } from "./Footer";
import { AgentDemoModal } from "./AgentDemoModal";

export function LandingPageClient() {
  const [demoDomain, setDemoDomain] = useState("yourcompany.com");
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  const handleLaunchDemo = (domain: string) => {
    setDemoDomain(domain || "yourcompany.com");
    setIsDemoModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-[#0A0A0A] font-sans selection:bg-[#FA651E]/20 selection:text-[#FA651E] antialiased">
      {/* Navigation */}
      <Navbar />

      {/* Main Content Sections */}
      <main>
        {/* 1. Hero Section */}
        <HeroSection onLaunchDemo={handleLaunchDemo} />

        {/* 2. Customer Trust Logo Bar */}
        <TrustBar />

        {/* 3. 4-Stage Product Showcase */}
        <ShowcaseSection onLaunchDemo={() => handleLaunchDemo("provenance.io")} />

        {/* 4. 3-Step Setup Walkthrough */}
        <SetupWalkthroughSection />

        {/* 5. Capability Bento Grid */}
        <OutreachBentoGrid />

        {/* 6. Unified-Agent Venn Diagram Stack Replacement */}
        <VennSection />

        {/* 7. Metrics & Testimonials */}
        <MetricsAndTestimonials />

        {/* 8. Integrations Hub */}
        <IntegrationsSection />

        {/* 9. Simple Pricing Plans */}
        <PricingSection />

        {/* 10. Final Call-To-Action Banner */}
        <FinalCTASection onLaunchDemo={handleLaunchDemo} />
      </main>

      {/* Footer */}
      <Footer />

      {/* Interactive Website Scanner / AI Agent Launcher Modal */}
      <AgentDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        domain={demoDomain}
      />
    </div>
  );
}
