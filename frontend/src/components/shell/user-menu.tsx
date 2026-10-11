"use client";

import React from "react";
import { useAppClerk } from "@/lib/auth/clerk-adapter";
import { User, LogOut, ShieldCheck, Building, ChevronsUpDown } from "lucide-react";
import { useUserStore } from "@/lib/store/user-store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface UserMenuProps {
  isCollapsed?: boolean;
}

export function UserMenu({ isCollapsed = false }: UserMenuProps) {
  const { signOut } = useAppClerk();
  const email = useUserStore((s) => s.email);
  const role = useUserStore((s) => s.role);
  const orgName = useUserStore((s) => s.orgName);
  const subscriptionTier = useUserStore((s) => s.subscriptionTier);
  const isPlatformAdmin = useUserStore((s) => s.isPlatformAdmin);

  const displayRole = role ? role.replace("_", " ") : "Member";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {isCollapsed ? (
          <Button
            variant="ghost"
            size="sm"
            className="flex h-9 w-9 items-center justify-center rounded-xl p-0 hover:bg-neutral-100 text-neutral-700 mx-auto"
            title={email || "User profile"}
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-orange-100 to-rose-100 text-[#FA651E] font-bold text-xs border border-orange-200/70">
              <User className="h-3.5 w-3.5" />
            </div>
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className="flex w-full items-center justify-between gap-2.5 rounded-xl px-2.5 py-2 h-auto hover:bg-neutral-100/80 transition-colors text-left"
          >
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-orange-100 to-rose-100 text-[#FA651E] font-bold text-xs border border-orange-200/70">
                <User className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <span className="block truncate text-xs font-semibold leading-tight text-neutral-900">
                  {email ? email.split("@")[0] : "User"}
                </span>
                <span className="block truncate text-[10px] text-neutral-500 capitalize">
                  {orgName || "Provenance"} · {displayRole}
                </span>
              </div>
            </div>
            <ChevronsUpDown className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
          </Button>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={isCollapsed ? "start" : "end"}
        side={isCollapsed ? "right" : "top"}
        sideOffset={8}
        className="w-56 rounded-2xl border border-neutral-200/80 bg-white p-1.5 shadow-lg"
      >
        <DropdownMenuLabel className="font-normal px-2.5 py-2">
          <div className="flex flex-col space-y-1">
            <p className="text-xs font-semibold leading-none text-neutral-900 truncate">
              {email || "Signed in"}
            </p>
            <div className="flex items-center gap-1.5 pt-1 text-neutral-500">
              <Building className="h-3 w-3 shrink-0" />
              <p className="text-[11px] leading-none truncate">
                {orgName || "Default Organization"}
              </p>
            </div>
            {subscriptionTier && (
              <Badge variant="outline" className="w-fit text-[10px] mt-1 capitalize rounded-md">
                Tier: {subscriptionTier}
              </Badge>
            )}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="my-1 border-neutral-100" />
        {isPlatformAdmin && (
          <>
            <DropdownMenuItem asChild>
              <a href="/admin" className="flex items-center text-xs text-amber-600 font-medium px-2.5 py-1.5 rounded-lg cursor-pointer hover:bg-neutral-50">
                <ShieldCheck className="mr-2 h-3.5 w-3.5" />
                Platform Admin Portal
              </a>
            </DropdownMenuItem>
            <DropdownMenuSeparator className="my-1 border-neutral-100" />
          </>
        )}
        <DropdownMenuItem
          className="text-xs text-rose-600 font-medium focus:bg-rose-50 focus:text-rose-700 cursor-pointer px-2.5 py-1.5 rounded-lg"
          onClick={() => signOut({ redirectUrl: "/sign-in" })}
        >
          <LogOut className="mr-2 h-3.5 w-3.5" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
