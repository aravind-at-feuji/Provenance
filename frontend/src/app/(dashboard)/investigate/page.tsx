"use client";

import React from "react";
import { InvestigationWorkspace } from "@/components/investigate/investigation-workspace";

export default function InvestigatePage(): React.JSX.Element {
  return (
    <div className="space-y-6">
      <InvestigationWorkspace />
    </div>
  );
}
