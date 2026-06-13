import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  Boxes,
  BadgeCheck,
  Briefcase,
  Crosshair,
  FlaskConical,
  Gamepad2,
  ListChecks,
  Menu,
  ScrollText,
  Search,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";
import racesData from "./data/races.json";
import careersData from "./data/careers.json";
import combatData from "./data/combat.json";
import benefitsData from "./data/benefits.json";
import abilitiesData from "./data/abilities.json";
import skillsData from "./data/skills.json";
import spellsData from "./data/spells.json";
import itemsData from "./data/items.json";
import metaData from "./data/meta.json";
import "./styles.css";

type TabId = "races" | "careers" | "game" | "features" | "skills" | "spells" | "items";

type Race = {
  id: string;
  name: string;
  bookPage: number;
  pdfPage: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  source?: string;
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
  pageStart?: number;
  pageEnd?: number;
  source?: string;
  summary: string;
  rules: string[];
};

type Career = {
  id: string;
  name: string;
  prerequisites: string;
  startingOnly: boolean;
  restrictedSecondCareer: boolean;
  spellcasting: boolean;
  summary: string;
  starting: {
    abilities: string;
    connections: string;
    militarySkills: string;
    occupationalSkills: string;
    spells: string;
    special: string;
    notes: string;
    assets: string;
  };
  progression: {
    abilities: string;
    connections: string;
    militarySkills: string;
    occupationalSkills: string;
    spells: string;
  };
  bookPage?: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  source: string;
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
  bookPage?: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  description: string;
  careers: string[];
  tags: string[];
};

type Feature = {
  id: string;
  name: string;
  type: "Archetype Benefit" | "Ability";
  archetype?: string;
  prerequisite?: string;
  bookPage?: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  source: string;
  description: string;
  tags: string[];
};

type Skill = {
  id: string;
  name: string;
  category: "Military" | "Occupational" | "General";
  governingStat: string;
  general: boolean;
  summary: string;
  description: string;
  untrained: string;
  use: string;
  bookPage?: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  source: string;
};

type Item = {
  id: string;
  name: string;
  category: string;
  price: string;
  bookPage?: number;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  source: string;
  fields: Record<string, string>;
  description: string;
  specialRules: string;
};

type AnyEntry = Race | Career | CombatCard | Feature | Skill | Spell | Item;

const races = racesData as unknown as Race[];
const careers = careersData as unknown as Career[];
const game = combatData as unknown as CombatCard[];
const benefits = benefitsData as unknown as Feature[];
const abilities = abilitiesData as unknown as Feature[];
const features = [...benefits, ...abilities].sort((a, b) => a.name.localeCompare(b.name));
const skills = skillsData as unknown as Skill[];
const spells = spellsData as unknown as Spell[];
const items = itemsData as unknown as Item[];
const meta = metaData as unknown as { counts: Record<string, number>; source: string };

const tabs = [
  { id: "races", label: "Races", icon: Users, count: races.length },
  { id: "careers", label: "Careers", icon: Briefcase, count: careers.length },
  { id: "game", label: "Game", icon: Gamepad2, count: game.length },
  { id: "features", label: "Benefits & Abilities", icon: BadgeCheck, count: features.length },
  { id: "skills", label: "Skills", icon: ListChecks, count: skills.length },
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
  if (tab === "game") return (entry as CombatCard).title;
  return (entry as Race | Career | Feature | Skill | Spell | Item).name;
}

function pageLabel(entry: { bookPage?: number; pageStart?: number; pageEnd?: number }): string {
  const start = entry.pageStart ?? entry.bookPage;
  if (!start) return "";
  const end = entry.pageEnd ?? start;
  return end > start ? `pp. ${start}-${end}` : `p. ${start}`;
}

function entrySubtitle(entry: AnyEntry, tab: TabId): string {
  if (tab === "races") {
    const race = entry as Race;
    return `${race.baseSize} base · ${pageLabel(race)}`;
  }
  if (tab === "careers") {
    const career = entry as Career;
    return `${career.prerequisites || "No prerequisites"} · ${pageLabel(career)}`;
  }
  if (tab === "game") {
    const card = entry as CombatCard;
    return `${card.category} · ${pageLabel(card)}`;
  }
  if (tab === "skills") {
    const skill = entry as Skill;
    return `${skill.category} · ${skill.governingStat} · ${pageLabel(skill)}`;
  }
  if (tab === "spells") {
    const spell = entry as Spell;
    return `COST ${spell.cost} · RNG ${spell.range} · POW ${spell.pow} · ${pageLabel(spell)}`;
  }
  if (tab === "features") {
    const feature = entry as Feature;
    const label = feature.type === "Archetype Benefit"
      ? `${feature.type} · ${feature.archetype}`
      : `${feature.type}${feature.prerequisite ? ` · Prereq: ${feature.prerequisite}` : ""}`;
    return `${label} · ${pageLabel(feature)}`;
  }
  const item = entry as Item;
  return `${item.category} · ${item.price} · ${pageLabel(item)}`;
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("spells");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [spellCost, setSpellCost] = useState("all");
  const [spellMode, setSpellMode] = useState("all");
  const [spellCareer, setSpellCareer] = useState("all");
  const [itemCategory, setItemCategory] = useState("all");
  const [gameCategory, setGameCategory] = useState("all");
  const [careerType, setCareerType] = useState("all");
  const [featureType, setFeatureType] = useState("all");
  const [featureTag, setFeatureTag] = useState("all");
  const [skillCategory, setSkillCategory] = useState("all");
  const [detailedOnly, setDetailedOnly] = useState(false);

  const itemCategories = useMemo(() => unique(items.map((item) => item.category)), []);
  const gameCategories = useMemo(() => unique(game.map((card) => card.category)), []);
  const featureTags = useMemo(() => unique(features.flatMap((feature) => feature.tags)), []);
  const spellCosts = useMemo(() => unique(spells.map((spell) => spell.cost)).sort((a, b) => Number(a.replace("+", "")) - Number(b.replace("+", ""))), []);
  const spellCareers = useMemo(() => unique(spells.flatMap((spell) => spell.careers ?? [])), []);
  const skillCategories = useMemo(() => unique(skills.map((skill) => skill.category)), []);

  const currentEntries = useMemo<AnyEntry[]>(() => {
    const search = query.trim().toLowerCase();
    if (activeTab === "races") {
      return races.filter((race) =>
        matches(search, [race.name, race.summary, race.archetypes.join(" "), race.traits.join(" "), race.languages]),
      );
    }
    if (activeTab === "careers") {
      return careers.filter((career) => {
        const typeOk =
          careerType === "all" ||
          (careerType === "spellcasting" && career.spellcasting) ||
          (careerType === "startingOnly" && career.startingOnly) ||
          (careerType === "restricted" && career.restrictedSecondCareer);
        return (
          typeOk &&
          matches(search, [
            career.name,
            career.prerequisites,
            career.summary,
            career.starting.abilities,
            career.starting.connections,
            career.starting.militarySkills,
            career.starting.occupationalSkills,
            career.starting.spells,
            career.starting.special,
            career.starting.assets,
            Object.values(career.progression).join(" "),
          ])
        );
      });
    }
    if (activeTab === "game") {
      return game.filter((card) => {
        const categoryOk = gameCategory === "all" || card.category === gameCategory;
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
    if (activeTab === "skills") {
      return skills.filter((skill) => {
        const categoryOk = skillCategory === "all" || skill.category === skillCategory;
        return categoryOk && matches(search, [skill.name, skill.category, skill.governingStat, skill.summary, skill.description, skill.untrained, skill.use]);
      });
    }
    if (activeTab === "spells") {
      return spells.filter((spell) => {
        const costOk = spellCost === "all" || spell.cost === spellCost;
        const careerOk = spellCareer === "all" || (spell.careers ?? []).includes(spellCareer);
        const modeOk =
          spellMode === "all" ||
          (spellMode === "upkeep" && spell.upkeep) ||
          (spellMode === "offensive" && spell.offensive) ||
          (spellMode === "utility" && !spell.offensive);
        return (
          costOk &&
          careerOk &&
          modeOk &&
          matches(search, [spell.name, spell.description, (spell.careers ?? []).join(" "), spell.tags.join(" "), spell.range, spell.aoe, spell.pow])
        );
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
  }, [activeTab, query, spellCost, spellMode, spellCareer, itemCategory, gameCategory, careerType, featureType, featureTag, skillCategory, detailedOnly]);

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
    if (activeTab === "careers") {
      return (
        <label className="filterControl">
          <Briefcase size={16} />
          <select value={careerType} onChange={(event) => setCareerType(event.target.value)}>
            <option value="all">All careers</option>
            <option value="spellcasting">Spellcasting careers</option>
            <option value="startingOnly">Starting-career only</option>
            <option value="restricted">Restricted second career</option>
          </select>
        </label>
      );
    }
    if (activeTab === "game") {
      return (
        <label className="filterControl">
          <Crosshair size={16} />
          <select value={gameCategory} onChange={(event) => setGameCategory(event.target.value)}>
            <option value="all">All game categories</option>
            {gameCategories.map((category) => (
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
    if (activeTab === "skills") {
      return (
        <label className="filterControl">
          <ListChecks size={16} />
          <select value={skillCategory} onChange={(event) => setSkillCategory(event.target.value)}>
            <option value="all">All skill categories</option>
            {skillCategories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
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
          <label className="filterControl">
            <Users size={16} />
            <select value={spellCareer} onChange={(event) => setSpellCareer(event.target.value)}>
              <option value="all">All careers</option>
              {spellCareers.map((career) => (
                <option key={career} value={career}>
                  {career}
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
    if (activeTab === "careers") return <CareerDetail career={entry as Career} />;
    if (activeTab === "game") return <GameDetail card={entry as CombatCard} />;
    if (activeTab === "features") return <FeatureDetail feature={entry as Feature} />;
    if (activeTab === "skills") return <SkillDetail skill={entry as Skill} />;
    if (activeTab === "spells") return <SpellDetail spell={entry as Spell} />;
    return <ItemDetail item={entry as Item} />;
  }
}

function RaceDetail({ race }: { race: Race }) {
  return (
    <>
      <DetailHeader icon={<Users size={22} />} title={race.name} subtitle={`Core Rules ${pageLabel(race)}`} />
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

function CareerDetail({ career }: { career: Career }) {
  const startingRules = compactRules([
    ["Abilities", career.starting.abilities],
    ["Connections", career.starting.connections],
    ["Military Skills", career.starting.militarySkills],
    ["Occupational Skills", career.starting.occupationalSkills],
    ["Spells", career.starting.spells],
    ["Special", career.starting.special],
    ["Assets", career.starting.assets],
  ]);
  const progressionRules = compactRules([
    ["Abilities", career.progression.abilities],
    ["Connections", career.progression.connections],
    ["Military Skills", career.progression.militarySkills],
    ["Occupational Skills", career.progression.occupationalSkills],
    ["Spells", career.progression.spells],
  ]);

  return (
    <>
      <DetailHeader icon={<Briefcase size={22} />} title={career.name} subtitle={`Career · Core Rules ${pageLabel(career)}`} />
      {career.summary && <p className="lead">{career.summary}</p>}
      <div className="factGrid">
        <Fact label="Prerequisites" value={career.prerequisites || "None"} />
        <Fact label="Spellcasting" value={career.spellcasting ? "Yes" : "No"} />
        <Fact label="Starting Only" value={career.startingOnly ? "Yes" : "No"} />
        <Fact label="Restricted Pairing" value={career.restrictedSecondCareer ? "Yes" : "No"} />
      </div>
      <h3>Starting Package</h3>
      <RuleList rules={startingRules} />
      <h3>Career Options</h3>
      <RuleList rules={progressionRules} />
      <SourceFoot source={career.source} />
    </>
  );
}

function GameDetail({ card }: { card: CombatCard }) {
  return (
    <>
      <DetailHeader icon={<Gamepad2 size={22} />} title={card.title} subtitle={`${card.category} · Core Rules ${pageLabel(card)}`} />
      <p className="lead">{card.summary}</p>
      <RuleList rules={card.rules} />
    </>
  );
}

function SpellDetail({ spell }: { spell: Spell }) {
  return (
    <>
      <DetailHeader icon={<Sparkles size={22} />} title={spell.name} subtitle={`Core Rules ${pageLabel(spell)}`} />
      <div className="spellStrip">
        <Fact label="Cost" value={spell.cost} />
        <Fact label="Range" value={spell.range} />
        <Fact label="AOE" value={spell.aoe} />
        <Fact label="POW" value={spell.pow} />
        <Fact label="Upkeep" value={spell.upkeep ? "Yes" : "No"} />
        <Fact label="Offensive" value={spell.offensiveMode} />
        <Fact label="Careers" value={(spell.careers ?? []).join(", ") || "Unlisted"} />
      </div>
      <p className="bodyText">{spell.description}</p>
      <TagList tags={spell.tags} />
      <SourceFoot source={spell.source} />
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
      <SourceFoot source={feature.source} />
    </>
  );
}

function SkillDetail({ skill }: { skill: Skill }) {
  return (
    <>
      <DetailHeader icon={<ListChecks size={22} />} title={skill.name} subtitle={`${skill.category} Skill · Core Rules ${pageLabel(skill)}`} />
      <div className="factGrid">
        <Fact label="Category" value={skill.category} />
        <Fact label="Governing Stat" value={skill.governingStat} />
        <Fact label="General Skill" value={skill.general ? "Yes" : "No"} />
      </div>
      {skill.description && <p className="lead">{skill.description}</p>}
      {skill.untrained && (
        <>
          <h3>Untrained Use</h3>
          <TextFlow text={skill.untrained} />
        </>
      )}
      {skill.use && (
        <>
          <h3>Skill Rolls</h3>
          <TextFlow text={skill.use} />
        </>
      )}
      <SourceFoot source={skill.source} />
    </>
  );
}

function ItemDetail({ item }: { item: Item }) {
  return (
    <>
      <DetailHeader icon={<Boxes size={22} />} title={item.name} subtitle={`${item.category} · ${item.price} · Core Rules ${pageLabel(item)}`} />
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
      <SourceFoot source={item.source} />
    </>
  );
}

function SourceFoot({ source }: { source: string }) {
  return (
    <div className="sourceFoot">
      <ScrollText size={15} />
      <span>{source}</span>
    </div>
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
  if (!rules.length) return <p className="bodyText muted">No additional entry data.</p>;
  return (
    <ul className="ruleList">
      {rules.map((rule) => (
        <li key={rule}>{rule}</li>
      ))}
    </ul>
  );
}

function TextFlow({ text }: { text: string }) {
  const blocks = textBlocks(text);
  return (
    <div className="textFlow">
      {blocks.map((block, index) => (
        <p key={`${index}-${block.slice(0, 20)}`} className={isTextHeading(block) ? "textBlockHeading" : "bodyText"}>
          {block}
        </p>
      ))}
    </div>
  );
}

function compactRules(values: Array<[string, string]>): string[] {
  return values.filter(([, value]) => Boolean(value)).map(([label, value]) => `${label}: ${value}`);
}

function textBlocks(text: string): string[] {
  const value = String(text ?? "")
    .replace(/\s+/g, " ")
    .replace(/\b(Target Number(?: - [^:]+)?):/g, "\n$1:\n")
    .replace(/\b(Roll Result(?: - [^:]+)?):/g, "\n$1:\n")
    .replace(/\b(Result Modifier(?: - [^:]+)?):/g, "\n$1:\n")
    .replace(/\b(Disguise target numbers - creation circumstances):/gi, "\n$1:\n")
    .replace(
      /\b(Assisted [A-Z][A-Za-z ]+ Rolls|Game Master Notes|Substance Identification|Craft Alchemical Items|Field Alchemy|Ingredient Extraction|Identifying Tracks|Steadying Nerves)\s*:/g,
      "\n$1:\n",
    )
    .trim();

  return value
    .split(/\n+/)
    .map((block) => block.trim())
    .filter(Boolean)
    .flatMap(splitLongTextBlock);
}

function splitLongTextBlock(block: string): string[] {
  if (block.length <= 520 || isTextHeading(block)) return [block];
  const sentences = block.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g) ?? [block];
  if (sentences.length <= 1) {
    const tableRows = block
      .split(/(?=\b(?:No Roll|No roll necessary|Automatic success|Succeed|Fail|Win by|Equal Result|\d+d6|[+-]\d|Subject['’]s|Target['’]s)\b)/g)
      .map((item) => item.trim())
      .filter(Boolean);
    if (tableRows.length > 1) return packTextBlocks(tableRows, 420);
  }
  const chunks: string[] = [];
  let current = "";

  for (const sentence of sentences.map((item) => item.trim()).filter(Boolean)) {
    const next = current ? `${current} ${sentence}` : sentence;
    if (next.length > 520 && current) {
      chunks.push(current);
      current = sentence;
    } else {
      current = next;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

function packTextBlocks(blocks: string[], maxLength: number): string[] {
  const chunks: string[] = [];
  let current = "";
  for (const block of blocks) {
    const next = current ? `${current} ${block}` : block;
    if (next.length > maxLength && current) {
      chunks.push(current);
      current = block;
    } else {
      current = next;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

function isTextHeading(block: string): boolean {
  return /:$/.test(block) && block.length < 90;
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
