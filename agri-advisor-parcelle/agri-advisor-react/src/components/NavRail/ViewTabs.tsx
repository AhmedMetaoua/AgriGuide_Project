import type { AppView } from "./viewTypes";
import "./ViewTabs.css";

const TABS: { id: AppView; label: string; icon: string }[] = [
  { id: "carte", label: "Carte", icon: "🗺️" },
  { id: "agriculture", label: "Conseiller", icon: "🌱" },
];

interface ViewTabsProps {
  active: AppView;
  onSelect: (view: AppView) => void;
}

export function ViewTabs({ active, onSelect }: ViewTabsProps) {
  return (
    <div className="view-tabs">
      {TABS.map((t) => (
        <button
          key={t.id}
          className={`view-tab${t.id === active ? " active" : ""}`}
          onClick={() => onSelect(t.id)}
        >
          <span>{t.icon}</span>
          {t.label}
        </button>
      ))}
    </div>
  );
}
