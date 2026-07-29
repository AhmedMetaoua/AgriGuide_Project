import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LineChart, Check, CheckCircle2, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";

export const Route = createFileRoute("/business")({
  head: () => ({
    meta: [
      { title: "Conseiller Business — AgriGuide" },
      { name: "description", content: "Simulez votre budget et comparez trois scénarios de cultures adaptés à votre exploitation." },
      { property: "og:title", content: "Conseiller Business — AgriGuide" },
      { property: "og:description", content: "Comparez trois scénarios pour tirer le meilleur de votre budget." },
    ],
  }),
  component: Page,
});

type Scenario = {
  name: string;
  desc: string;
  crop: string;
  hectares: number;
  profit: number;
  risk: "Faible" | "Modéré" | "Élevé";
};

function scenarios(budget: number): Scenario[] {
  const b = budget / 1000;
  return [
    { name: "Prudent", desc: "Blé + luzerne, revenus stables.", crop: "Blé & luzerne", hectares: Math.round(b * 0.9), profit: Math.round(budget * 1.35), risk: "Faible" },
    { name: "Équilibré", desc: "Rotation blé, colza, tournesol.", crop: "Blé, colza, tournesol", hectares: Math.round(b * 1.1), profit: Math.round(budget * 1.7), risk: "Modéré" },
    { name: "Ambitieux", desc: "Cultures spécialisées à forte valeur.", crop: "Colza HOLL, lentilles bio", hectares: Math.round(b * 1.25), profit: Math.round(budget * 2.2), risk: "Élevé" },
  ];
}

const riskColor: Record<Scenario["risk"], string> = {
  "Faible": "bg-harvest/15 text-harvest border-harvest/30",
  "Modéré": "bg-waste/20 text-waste-foreground border-waste/40",
  "Élevé": "bg-destructive/10 text-destructive border-destructive/30",
};

function Page() {
  const [budget, setBudget] = useState(25000);
  const [selected, setSelected] = useState<Scenario | null>(null);
  const list = useMemo(() => scenarios(budget), [budget]);

  if (selected) {
    return (
      <AppShell>
        <div className="max-w-2xl mx-auto text-center">
          <div className="mx-auto h-16 w-16 rounded-full bg-harvest/20 text-harvest flex items-center justify-center">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <h1 className="mt-6 font-display text-3xl md:text-4xl font-semibold">Scénario confirmé</h1>
          <p className="mt-2 text-muted-foreground">
            Voici la répartition de vos hectares pour <b>{selected.name}</b>.
          </p>
        </div>

        <div className="card-soft p-6 mt-8 max-w-2xl mx-auto">
          <div className="text-sm text-muted-foreground">Répartition proposée</div>
          <div className="mt-4 space-y-3">
            {selected.crop.split(",").map((c, i, arr) => {
              const share = i === arr.length - 1 ? 100 - (arr.length - 1) * Math.floor(100 / arr.length) : Math.floor(100 / arr.length);
              const ha = Math.round((selected.hectares * share) / 100);
              return (
                <div key={c}>
                  <div className="flex justify-between text-sm font-medium">
                    <span>{c.trim()}</span>
                    <span className="text-muted-foreground">{ha} ha · {share}%</span>
                  </div>
                  <div className="mt-1 h-3 rounded-full bg-secondary overflow-hidden">
                    <div className="h-full bg-gradient-hero" style={{ width: `${share}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-6 rounded-2xl bg-secondary/60 p-4 flex items-center justify-between">
            <div>
              <div className="text-xs text-muted-foreground">Profit estimé</div>
              <div className="font-display text-2xl font-semibold">{selected.profit.toLocaleString("fr-FR")} €</div>
            </div>
            <Badge className={`border ${riskColor[selected.risk]}`}>Risque {selected.risk}</Badge>
          </div>
        </div>

        <div className="mt-6 flex justify-center">
          <Button variant="outline" onClick={() => setSelected(null)} className="rounded-xl">
            Choisir un autre scénario
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-8">
        <div className="h-11 w-11 rounded-2xl bg-earth/15 text-earth flex items-center justify-center">
          <LineChart className="h-6 w-6" />
        </div>
        <div>
          <h1 className="font-display text-3xl md:text-4xl font-semibold leading-none">Conseiller Business</h1>
          <p className="text-muted-foreground mt-1">Simulez vos revenus selon votre budget.</p>
        </div>
      </div>

      <div className="card-soft p-6 md:p-8">
        <div className="flex items-baseline justify-between">
          <div className="text-sm text-muted-foreground">Votre budget de départ</div>
          <div className="font-display text-3xl font-semibold text-primary">{budget.toLocaleString("fr-FR")} €</div>
        </div>
        <Slider
          value={[budget]}
          onValueChange={(v) => setBudget(v[0])}
          min={5000}
          max={80000}
          step={1000}
          className="mt-6"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-2">
          <span>5 000 €</span>
          <span>80 000 €</span>
        </div>
      </div>

      <h2 className="font-display text-2xl font-semibold mt-10 mb-4">Trois scénarios pour vous</h2>
      <div className="grid gap-5 md:grid-cols-3">
        {list.map((s) => (
          <div key={s.name} className="card-soft p-6 flex flex-col">
            <div className="flex items-center justify-between">
              <div className="font-display text-xl font-semibold">{s.name}</div>
              <Badge className={`border ${riskColor[s.risk]}`}>Risque {s.risk}</Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{s.desc}</p>

            <div className="mt-5 space-y-3 text-sm">
              <Row label="Culture" value={s.crop} />
              <Row label="Surface" value={`${s.hectares} ha`} />
              <Row label="Profit estimé" value={`${s.profit.toLocaleString("fr-FR")} €`} accent />
            </div>

            <div className="mt-auto pt-6">
              <Button className="w-full rounded-xl h-12" onClick={() => setSelected(s)}>
                <Check className="h-4 w-4 mr-2" /> Choisir ce scénario
              </Button>
            </div>
            {s.name === "Équilibré" && (
              <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-primary justify-center">
                <TrendingUp className="h-3 w-3" /> Recommandé pour vous
              </div>
            )}
          </div>
        ))}
      </div>
    </AppShell>
  );
}

function Row({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border pb-2 last:border-none">
      <span className="text-muted-foreground">{label}</span>
      <span className={accent ? "font-display text-lg font-semibold text-primary" : "font-medium"}>{value}</span>
    </div>
  );
}
