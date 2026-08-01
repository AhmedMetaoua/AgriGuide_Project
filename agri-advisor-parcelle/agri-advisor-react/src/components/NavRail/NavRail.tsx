import "./NavRail.css";

// URL of the main "AgriGuide" app (frontend/). Override in prod via VITE_AGRIGUIDE_URL;
// defaults to the local Vite/TanStack dev server.
const AGRIGUIDE_URL = import.meta.env.VITE_AGRIGUIDE_URL ?? "http://localhost:8080";

interface NavItem {
  key: string;
  icon: string;
  label: string;
  href?: string; // external -> goes back to AgriGuide
  active?: boolean;
}

const ITEMS: NavItem[] = [
  { key: "accueil", icon: "🏠", label: "Accueil", href: `${AGRIGUIDE_URL}/dashboard` },
  { key: "cultures", icon: "🌱", label: "Cultures", active: true },
  { key: "regles", icon: "📜", label: "Règles", href: `${AGRIGUIDE_URL}/regulation` },
  { key: "budget", icon: "📈", label: "Budget", href: `${AGRIGUIDE_URL}/business` },
  { key: "aujourdhui", icon: "🗓️", label: "Aujourd'hui", href: `${AGRIGUIDE_URL}/aujourd-hui` },
  { key: "marche", icon: "🏪", label: "Marché", href: `${AGRIGUIDE_URL}/marketplace` },
];

export function NavRail() {
  return (
    <nav className="navrail">
      <a href={`${AGRIGUIDE_URL}/dashboard`} className="navrail-brand">
        <div className="bicon">🌿</div>
        <div>
          <h1>AgriMent</h1>
          <p>Votre allié au quotidien</p>
        </div>
      </a>

      <div className="navrail-items">
        {ITEMS.map((item) =>
          item.href ? (
            <a key={item.key} className="navrail-item" href={item.href}>
              <span className="navrail-icon">{item.icon}</span>
              <span className="navrail-label">{item.label}</span>
            </a>
          ) : (
            <div key={item.key} className="navrail-item active" aria-current="page">
              <span className="navrail-icon">{item.icon}</span>
              <span className="navrail-label">{item.label}</span>
            </div>
          ),
        )}
      </div>

      <div className="navrail-user">
        <div className="navrail-avatar">JD</div>
        <div>
          <div className="navrail-user-name">Jean Demo</div>
          <div className="navrail-user-role">Agriculteur</div>
        </div>
      </div>
    </nav>
  );
}
