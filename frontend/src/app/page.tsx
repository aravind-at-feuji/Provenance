import type { Metadata } from "next";
import { LandingPageClient } from "@/components/landing/LandingPageClient";

export const metadata: Metadata = {
  title: "Provenance — Supply Chain Risk Intelligence & Exposure Mapping",
  description:
    "Autonomous multi-tier supply chain risk intelligence. Monitor regulatory, sanctions, and geopolitical shocks; resolve entities across your supplier graph; score dollar exposure deterministically with cited evidence chains.",
};

/**
 * Provenance Landing Page Root Route
 */
export default function RootPage() {
  return <LandingPageClient />;
}
