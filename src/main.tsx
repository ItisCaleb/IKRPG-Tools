import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  Boxes,
  BadgeCheck,
  Crosshair,
  FlaskConical,
  Menu,
  ScrollText,
  Search,
  Shield,
  Sparkles,
  Swords,
  Users,
} from "lucide-react";
import racesData from "./data/races.json";
import combatData from "./data/combat.json";
import benefitsData from "./data/benefits.json";
import abilitiesData from "./data/abilities.json";
import spellsData from "./data/spells.json";
import itemsData from "./data/items.json";
import metaData from "./data/meta.json";
import "./styles.css";

type TabId = "races" | "combat" | "features" | "spells" | "items";

type Race = {
  id: string;
  name: string;
  bookPage: number;
  pdfPage: number;
  baseSize: string;
  summary: string;
  archetypes: string[];
  languages: string;
  height: string;
  weight: string;
  stats: Record<string, { start: number | string; hero: number | string; veteran: number | string; epic: number | string }>;
  traits: string[];
};

type CombatCard = {
  id: string;
  title: string;
  category: string;
  bookPage: number;
  summary: string;
  rules: string[];
};

type Spell = {
  id: string;
  name: string;
  rawName: string;
  cost: string;
  range: string;
  aoe: string;
  pow: string;
  upkeep: boolean;
  offensive: boolean;
  offensiveMode: string;
  source: string;
  description: string;
  tags: string[];
};

type Feature = {
  id: string;
  name: string;
  type: "Archetype Benefit" | "Ability";
  archetype?: string;
  prerequisite?: string;
  bookPage?: number;
  source: string;
  description: string;
  tags: string[];
};

type Item = {
  id: string;
  name: string;
  category: string;
  price: string;
  source: string;
  fields: Record<string, string>;
  description: string;
  specialRules: string;
};

type AnyEntry = Race | CombatCard | Feature | Spell | Item;

const races = racesData as unknown as Race[];
const combat = combatData as unknown as CombatCard[];
const benefits = benefitsData as unknown as Feature[];
const abilities = abilitiesData as unknown as Feature[];
const features = [...benefits, ...abilities].sort((a, b) => a.name.localeCompare(b.name));
const spells = spellsData as unknown as Spell[];
const items = itemsData as unknown as Item[];
const meta = metaData as unknown as { counts: Record<string, number>; source: string };

const tabs = [
  { id: "races", label: "Races", icon: Users, count: races.length },
  { id: "combat", label: "Combat", icon: Swords, count: combat.length },
  { id: "features", label: "Benefits & Abilities", icon: BadgeCheck, count: features.length },
  { id: "spells", label: "Spells", icon: Sparkles, count: spells.length },
  { id: "items", label: "Items", icon: Boxes, count: items.length },
] as const;

const statOrder = ["PHY", "SPD", "STR", "AGL", "PRW", "POI", "INT", "ARC", "PER"];

function normalize(value: unknown): string {
  return String(value ?? "").toLowerCase();
}

function includesText(value: unknown, query: string): boolean {
  return normalize(value).includes(query);
}

function entryTitle(entry: AnyEntry, tab: TabId): string {
  if (tab === "combat") return (entry as CombatCard).title;
  return (entry as Race | Feature | Spell | Item).name;
}

function entrySubtitle(entry: AnyEntry, tab: TabId): string {
  if (tab === "races") return `${(entry as Race).baseSize} base · p. ${(entry as Race).bookPage}`;
  if (tab === "combat") return `${(entry as CombatCard).category} · p. ${(entry as CombatCard).bookPage}`;
  if (tab === "spells") {
    const spell = entry as Spell;
    return `COST ${spell.cost} · RNG ${spell.range} · POW ${spell.pow}`;
  }
  if (tab === "features") {
    const feature = entry as Feature;
    return feature.type === "Archetype Benefit"
      ? `${feature.type} · ${feature.archetype}`
      : `${feature.type}${feature.prerequisite ? ` · Prereq: ${feature.prerequisite}` : ""}`;
  }
  const item = entry as Item;
  return `${item.category} · ${item.price}`;
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("spells");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [spellCost, setSpellCost] = useState("all");
  const [spellMode, setSpellMode] = useState("all");
  const [itemCategory, setItemCategory] = useState("all");
  const [combatCategory, setCombatCategory] = useState("all");
  const [featureType, setFeatureType] = useState("all");
  const [featureTag, setFeatureTag] = useState("all");
  const [detailedOnly, setDetailedOnly] = useState(false);

  const itemCategories = useMemo(() => unique(items.map((item) => item.category)), []);
  const combatCategories = useMemo(() => unique(combat.map((card) => card.category)), []);
  const featureTags = useMemo(() => unique(features.flatMap((feature) => feature.tags)), []);
  const spellCosts = useMemo(() => unique(spells.map((spell) => spell.cost)).sort((a, b) => Number(a.replace("+", "")) - Number(b.replace("+", ""))), []);

  const currentEntries = useMemo<AnyEntry[]>(() => {
    const search = query.trim().toLowerCase();
    if (activeTab === "races") {
      return races.filter((race) =>
        matches(search, [race.name, race.summary, race.archetypes.join(" "), race.traits.join(" "), race.languages]),
      );
    }
    if (activeTab === "combat") {
      return combat.filter((card) => {
        const categoryOk = combatCategory === "all" || card.category === combatCategory;
        return categoryOk && matches(search, [card.title, card.category, card.summary, card.rules.join(" ")]);
      });
    }
    if (activeTab === "features") {
      return features.filter((feature) => {
        const typeOk = featureType === "all" || feature.type === featureType;
        const tagOk = featureTag === "all" || feature.tags.includes(featureTag);
        return (
          typeOk &&
          tagOk &&
          matches(search, [
            feature.name,
            feature.type,
            feature.archetype,
            feature.prerequisite,
            feature.description,
            feature.tags.join(" "),
          ])
        );
      });
    }
    if (activeTab === "spells") {
      return spells.filter((spell) => {
        const costOk = spellCost === "all" || spell.cost === spellCost;
        const modeOk =
          spellMode === "all" ||
          (spellMode === "upkeep" && spell.upkeep) ||
          (spellMode === "offensive" && spell.offensive) ||
          (spellMode === "utility" && !spell.offensive);
        return costOk && modeOk && matches(search, [spell.name, spell.description, spell.tags.join(" "), spell.range, spell.aoe, spell.pow]);
      });
    }
    return items.filter((item) => {
      const categoryOk = itemCategory === "all" || item.category === itemCategory;
      const detailOk = !detailedOnly || Boolean(item.description || item.specialRules);
      return (
        categoryOk &&
        detailOk &&
        matches(search, [item.name, item.category, item.price, item.description, item.specialRules, Object.values(item.fields).join(" ")])
      );
    });
  }, [activeTab, query, spellCost, spellMode, itemCategory, combatCategory, featureType, featureTag, detailedOnly]);

  const selected = useMemo(() => {
    if (selectedId) {
      const found = currentEntries.find((entry) => "id" in entry && entry.id === selectedId);
      if (found) return found;
    }
    return currentEntries[0] ?? null;
  }, [currentEntries, selectedId]);

  function switchTab(tab: TabId) {
    setActiveTab(tab);
    setSelectedId(null);
    setMobileMenuOpen(false);
  }

  return (
    <div className="appShell">
      <aside className={`rail ${mobileMenuOpen ? "railOpen" : ""}`}>
        <div className="brand">
          <div className="brandMark">
            <Shield size={22} />
          </div>
          <div>
            <strong>IKRPG Tools</strong>
            <span>Core Rules quick reference</span>
          </div>
        </div>

        <nav className="tabList" aria-label="Data categories">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={activeTab === tab.id ? "tabButton active" : "tabButton"}
                onClick={() => switchTab(tab.id)}
                title={tab.label}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
                <small>{tab.count}</small>
              </button>
            );
          })}
        </nav>

        <div className="sourceBox">
          <BookOpen size={16} />
          <span>{meta.source}</span>
        </div>
      </aside>
      {mobileMenuOpen && <button className="navScrim" aria-label="Close menu" onClick={() => setMobileMenuOpen(false)} />}

      <main className="workspace">
        <header className="topbar">
          <button className="iconButton mobileOnly" onClick={() => setMobileMenuOpen((value) => !value)} title="Toggle menu">
            <Menu size={20} />
          </button>
          <div className="searchBox">
            <Search size={18} />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setSelectedId(null);
              }}
              placeholder={`Search ${tabs.find((tab) => tab.id === activeTab)?.label ?? ""}...`}
            />
          </div>
          <div className="metaPills">
            <span>{currentEntries.length} results</span>
            <span>{meta.counts.itemDetails} item notes</span>
          </div>
        </header>

        <section className="filters">{renderFilters()}</section>

        <section className="contentGrid">
          <div className="listPane" aria-label="Entry list">
            {currentEntries.map((entry) => (
              <button
                key={`${activeTab}-${entry.id}`}
                className={selected && entry.id === selected.id ? "entryRow selected" : "entryRow"}
                onClick={() => setSelectedId(entry.id)}
              >
                <span>{entryTitle(entry, activeTab)}</span>
                <small>{entrySubtitle(entry, activeTab)}</small>
              </button>
            ))}
            {currentEntries.length === 0 && <div className="emptyState">No matching entries.</div>}
          </div>

          <article className="detailPane">{selected ? renderDetail(selected) : <div className="emptyState">Select an entry to start reading.</div>}</article>
        </section>
      </main>
    </div>
  );

  function renderFilters() {
    if (activeTab === "combat") {
      return (
        <label className="filterControl">
          <Crosshair size={16} />
          <select value={combatCategory} onChange={(event) => setCombatCategory(event.target.value)}>
            <option value="all">All combat categories</option>
            {combatCategories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
      );
    }
    if (activeTab === "features") {
      return (
        <>
          <label className="filterControl">
            <BadgeCheck size={16} />
            <select value={featureType} onChange={(event) => setFeatureType(event.target.value)}>
              <option value="all">All feature types</option>
              <option value="Archetype Benefit">Archetype Benefits</option>
              <option value="Ability">Abilities</option>
            </select>
          </label>
          <label className="filterControl">
            <ScrollText size={16} />
            <select value={featureTag} onChange={(event) => setFeatureTag(event.target.value)}>
              <option value="all">All tags</option>
              {featureTags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </label>
        </>
      );
    }
    if (activeTab === "spells") {
      return (
        <>
          <label className="filterControl">
            <FlaskConical size={16} />
            <select value={spellCost} onChange={(event) => setSpellCost(event.target.value)}>
              <option value="all">All COST values</option>
              {spellCosts.map((cost) => (
                <option key={cost} value={cost}>
                  COST {cost}
                </option>
              ))}
            </select>
          </label>
          <div className="segmented" role="group" aria-label="Spell mode">
            {[
              ["all", "All"],
              ["offensive", "Offensive"],
              ["upkeep", "Upkeep"],
              ["utility", "Utility"],
            ].map(([value, label]) => (
              <button key={value} className={spellMode === value ? "active" : ""} onClick={() => setSpellMode(value)}>
                {label}
              </button>
            ))}
          </div>
        </>
      );
    }
    if (activeTab === "items") {
      return (
        <>
          <label className="filterControl">
            <Boxes size={16} />
            <select value={itemCategory} onChange={(event) => setItemCategory(event.target.value)}>
              <option value="all">All item categories</option>
              {itemCategories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <label className="toggleControl">
            <input type="checkbox" checked={detailedOnly} onChange={(event) => setDetailedOnly(event.target.checked)} />
            <span>Only entries with descriptions</span>
          </label>
        </>
      );
    }
    return (
      <div className="hintLine">
        <Users size={16} />
        <span>Race data includes starting values, Hero/Veteran/Epic limits, languages, base size, and traits.</span>
      </div>
    );
  }

  function renderDetail(entry: AnyEntry) {
    if (activeTab === "races") return <RaceDetail race={entry as Race} />;
    if (activeTab === "combat") return <CombatDetail card={entry as CombatCard} />;
    if (activeTab === "features") return <FeatureDetail feature={entry as Feature} />;
    if (activeTab === "spells") return <SpellDetail spell={entry as Spell} />;
    return <ItemDetail item={entry as Item} />;
  }
}

function RaceDetail({ race }: { race: Race }) {
  return (
    <>
      <DetailHeader icon={<Users size={22} />} title={race.name} subtitle={`Book p. ${race.bookPage} · PDF p. ${race.pdfPage}`} />
      <p className="lead">{race.summary}</p>
      <div className="factGrid">
        <Fact label="Base" value={race.baseSize} />
        <Fact label="Archetypes" value={race.archetypes.join(", ")} />
        <Fact label="Languages" value={race.languages} />
        <Fact label="Height" value={race.height} />
        <Fact label="Weight" value={race.weight} />
      </div>
      <h3>Stats</h3>
      <div className="statTable">
        <div className="statHead">Stat</div>
        <div className="statHead">Start</div>
        <div className="statHead">Hero</div>
        <div className="statHead">Vet</div>
        <div className="statHead">Epic</div>
        {statOrder.map((stat) => (
          <React.Fragment key={stat}>
            <strong>{stat}</strong>
            <span>{race.stats[stat]?.start}</span>
            <span>{race.stats[stat]?.hero}</span>
            <span>{race.stats[stat]?.veteran}</span>
            <span>{race.stats[stat]?.epic}</span>
          </React.Fragment>
        ))}
      </div>
      <h3>Traits</h3>
      <RuleList rules={race.traits} />
    </>
  );
}

function CombatDetail({ card }: { card: CombatCard }) {
  return (
    <>
      <DetailHeader icon={<Swords size={22} />} title={card.title} subtitle={`${card.category} · Book p. ${card.bookPage}`} />
      <p className="lead">{card.summary}</p>
      <RuleList rules={card.rules} />
    </>
  );
}

function SpellDetail({ spell }: { spell: Spell }) {
  return (
    <>
      <DetailHeader icon={<Sparkles size={22} />} title={spell.name} subtitle={spell.source} />
      <div className="spellStrip">
        <Fact label="Cost" value={spell.cost} />
        <Fact label="Range" value={spell.range} />
        <Fact label="AOE" value={spell.aoe} />
        <Fact label="POW" value={spell.pow} />
        <Fact label="Upkeep" value={spell.upkeep ? "Yes" : "No"} />
        <Fact label="Offensive" value={spell.offensiveMode} />
      </div>
      <p className="bodyText">{spell.description}</p>
      <TagList tags={spell.tags} />
    </>
  );
}

function FeatureDetail({ feature }: { feature: Feature }) {
  const subtitle =
    feature.type === "Archetype Benefit"
      ? `${feature.type}${feature.archetype ? ` · ${feature.archetype}` : ""}`
      : `${feature.type}${feature.prerequisite ? ` · Prerequisite: ${feature.prerequisite}` : ""}`;

  return (
    <>
      <DetailHeader icon={<BadgeCheck size={22} />} title={feature.name} subtitle={subtitle} />
      <p className="bodyText">{feature.description}</p>
      <TagList tags={feature.tags} />
      <div className="sourceFoot">
        <ScrollText size={15} />
        <span>{feature.source}</span>
      </div>
    </>
  );
}

function ItemDetail({ item }: { item: Item }) {
  return (
    <>
      <DetailHeader icon={<Boxes size={22} />} title={item.name} subtitle={`${item.category} · ${item.price}`} />
      {Object.keys(item.fields).length > 0 && (
        <div className="fieldTable">
          {Object.entries(item.fields).map(([key, value]) => (
            <React.Fragment key={key}>
              <span>{fieldLabel(key)}</span>
              <strong>{value}</strong>
            </React.Fragment>
          ))}
        </div>
      )}
      {item.description ? (
        <>
          <h3>Description</h3>
          <p className="bodyText">{item.description}</p>
        </>
      ) : (
        <p className="bodyText muted">This item currently only has price-list data.</p>
      )}
      {item.specialRules && (
        <>
          <h3>Special Rules</h3>
          <p className="bodyText">{item.specialRules}</p>
        </>
      )}
      <div className="sourceFoot">
        <ScrollText size={15} />
        <span>{item.source}</span>
      </div>
    </>
  );
}

function DetailHeader({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <div className="detailHeader">
      <div className="detailIcon">{icon}</div>
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="fact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RuleList({ rules }: { rules: string[] }) {
  return (
    <ul className="ruleList">
      {rules.map((rule) => (
        <li key={rule}>{rule}</li>
      ))}
    </ul>
  );
}

function TagList({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <div className="tagList">
      {tags.map((tag) => (
        <span key={tag}>{tag}</span>
      ))}
    </div>
  );
}

function matches(query: string, values: unknown[]): boolean {
  if (!query) return true;
  return values.some((value) => includesText(value, query));
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

function fieldLabel(key: string): string {
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

createRoot(document.getElementById("root")!).render(<App />);
