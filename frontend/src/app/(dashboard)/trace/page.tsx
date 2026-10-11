"use client";

import React from "react";
import { AgentTraceWorkspace } from "@/components/investigate/agent-trace-workspace";

export default function TracePage(): React.JSX.Element {
  return (
    <div className="space-y-6">
      <AgentTraceWorkspace />
    </div>
  );
}
