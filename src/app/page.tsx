import Link from "next/link";

import { api, HydrateClient } from "@/trpc/server";
import { Button } from "@/components/ui/button";
import { ArrowRightIcon } from "lucide-react";

export default async function Home() {
  return (
    <HydrateClient>
      <div className="flex min-h-screen items-center justify-center flex-col gap-4">
        <h1 className="text-6xl font-bold"><span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-purple-500">
          AI Powered</span> Early Warning System</h1>
        <Link href="/platform/patients">
          <Button size="xl">Go to Platform <ArrowRightIcon className="w-4 h-4" /></Button>
        </Link>
      </div>
    </HydrateClient>
  );
}
