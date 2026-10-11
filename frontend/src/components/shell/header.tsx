"use client";

import React from "react";
import { PersonaSwitcher } from "./persona-switcher";
import { UserMenu } from "./user-menu";

export function Header() {
  return (
    <header className="sticky top-0 z-20 flex h-14 w-full items-center justify-between border-b border-border/70 bg-background/80 px-6 backdrop-blur-md">
      {/* Left Header Info */}
      <div className="flex items-center gap-3">
        <span className="hidden text-xs text-muted-foreground md:inline font-mono">
          Provenance Intelligence Platform
        </span>
      </div>

      {/* Right: Persona Switcher & User Menu */}
      <div className="flex items-center gap-3">
        <PersonaSwitcher />
        <UserMenu />
      </div>
    </header>
  );
}
