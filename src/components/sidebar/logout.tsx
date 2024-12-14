"use client";

import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { signOut } from "@/server/auth";

export const SidebarLogout = () => {
  return (
    <DropdownMenuItem onClick={() => {
      void signOut().then(() => {
        window.location.href = "/";
      })
    }}>
      <span>Sign out</span>
    </DropdownMenuItem>
  )
}