import { createFileRoute } from "@tanstack/react-router";
import { Loader2, Sprout } from "lucide-react";
import { useEffect } from "react";
import { AppShell } from "@/components/AppShell";

// This page used to host a static mock-up of the crop advisor. That advisor now
// lives in the standalone "Agri Advisor IA" app (agri-advisor-parcelle/agri-advisor-react),
// so anyone who lands on /agriculture directly (bookmark, stale link, etc.) gets
// bounced there instead of seeing the old placeholder content.
const AGRI_ADVISOR_URL = import.meta.env.VITE_AGRI_ADVISOR_URL ?? "http://localhost:5173";

export const Route = createFileRoute("/agriculture")({
  head: () => ({
    meta: [{ title: "Conseiller Agricole — AgriGuide" }],
  }),
  component: Page,
});

function Page() {
  useEffect(() => {
    window.location.href = AGRI_ADVISOR_URL;
  }, []);

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center gap-3 py-24 text-center text-muted-foreground">
        <Sprout className="h-8 w-8 text-primary" />
        <Loader2 className="h-5 w-5 animate-spin" />
        <p>Redirection vers votre conseiller agricole…</p>
        <a href={AGRI_ADVISOR_URL} className="text-sm text-primary underline">
          Cliquez ici si la redirection ne se fait pas automatiquement
        </a>
      </div>
    </AppShell>
  );
}