import { AppSidebar } from "@/components/sidebar"
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { auth } from "@/server/auth"
import { redirect } from "next/navigation";

export default async function Layout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="min-h-screen w-full">
        {children}
      </main>
    </SidebarProvider>
  )
}
