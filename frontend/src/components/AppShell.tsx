import { Link, useRouterState } from "@tanstack/react-router";
import { Home, Sprout, ScrollText, LineChart, CalendarDays, Store, Leaf } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/dashboard", label: "Accueil", icon: Home },
  { to: "/agriculture", label: "Cultures", icon: Sprout },
  { to: "/regulation", label: "Règles", icon: ScrollText },
  { to: "/business", label: "Budget", icon: LineChart },
  { to: "/aujourd-hui", label: "Aujourd'hui", icon: CalendarDays },
  { to: "/marketplace", label: "Marché", icon: Store },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0 md:pl-72">
      {/* Sidebar (desktop) */}
      <aside className="hidden md:flex fixed left-0 top-0 h-screen w-72 flex-col border-r border-border bg-card px-6 py-8 gap-2">
        <Link to="/dashboard" className="flex items-center gap-3 mb-8">
          <div className="h-11 w-11 rounded-2xl bg-gradient-hero flex items-center justify-center shadow-sm">
            <Leaf className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <div className="font-display text-xl font-semibold leading-none">AgriGuide</div>
            <div className="text-xs text-muted-foreground mt-1">Votre allié au quotidien</div>
          </div>
        </Link>
        <nav className="flex flex-col gap-1">
          {nav.map(({ to, label, icon: Icon }) => {
            const active = pathname === to || pathname.startsWith(to + "/");
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-4 py-3 text-base font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-foreground hover:bg-secondary",
                )}
              >
                <Icon className="h-5 w-5" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto rounded-2xl bg-gradient-warm p-4">
          <div className="text-sm font-semibold text-earth-foreground/90">Besoin d'aide ?</div>
          <p className="text-xs text-muted-foreground mt-1">Notre équipe répond du lundi au samedi.</p>
        </div>
      </aside>

      <main className="mx-auto max-w-6xl px-4 py-6 md:px-10 md:py-10">{children}</main>

      {/* Bottom nav (mobile) */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-card/95 backdrop-blur border-t border-border">
        <div className="grid grid-cols-6">
          {nav.map(({ to, label, icon: Icon }) => {
            const active = pathname === to || pathname.startsWith(to + "/");
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
                  active ? "text-primary" : "text-muted-foreground",
                )}
              >
                <Icon className="h-5 w-5" />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
