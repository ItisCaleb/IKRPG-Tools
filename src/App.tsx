import { useEffect, useMemo, useState } from "react";
import {
  BadgeCheck,
  BookOpen,
  Boxes,
  Briefcase,
  Crosshair,
  FlaskConical,
  Gamepad2,
  ListChecks,
  ScrollText,
  Search,
  Shield,
  Sparkles,
  Star,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { CareerDetail, FeatureDetail, GameDetail, ItemDetail, RaceDetail, SkillDetail, SpellDetail } from "./components/DetailViews";
import { careers, features, game, items, meta, races, skills, spells } from "./data";
import type { AnyEntry, Career, CombatCard, DataTabId, Feature, Item, ListedEntry, Race, Skill, Spell, TabId } from "./types";
import { entryKey, entrySubtitle, entryTitle, matches, unique } from "./utils";

const FAVORITES_STORAGE_KEY = "ikrpg-tools:favorites:v1";

type TabDefinition = {
  id: TabId;
  label: string;
  icon: LucideIcon;
  count: number;
};

type DataTabDefinition = TabDefinition & {
  id: DataTabId;
};

const dataTabs: DataTabDefinition[] = [
  { id: "races", label: "Races", icon: Users, count: races.length },
  { id: "careers", label: "Careers", icon: Briefcase, count: careers.length },
  { id: "game", label: "Game", icon: Gamepad2, count: game.length },
  { id: "features", label: "Benefits & Abilities", icon: BadgeCheck, count: features.length },
  { id: "skills", label: "Skills", icon: ListChecks, count: skills.length },
  { id: "spells", label: "Spells", icon: Sparkles, count: spells.length },
  { id: "items", label: "Items", icon: Boxes, count: items.length },
];

const dataTabLabels: Record<DataTabId, string> = {
  races: "Races",
  careers: "Careers",
  game: "Game",
  features: "Benefits & Abilities",
  skills: "Skills",
  spells: "Spells",
  items: "Items",
};

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>("spells");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(() => loadFavorites());
  const [favoriteCategory, setFavoriteCategory] = useState<DataTabId | "all">("all");
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

  useEffect(() => {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([...favoriteIds]));
  }, [favoriteIds]);

  const itemCategories = useMemo(() => unique(items.map((item) => item.category)), []);
  const gameCategories = useMemo(() => unique(game.map((card) => card.category)), []);
  const featureTags = useMemo(() => unique(features.flatMap((feature) => feature.tags)), []);
  const spellCosts = useMemo(
    () => unique(spells.map((spell) => spell.cost)).sort((a, b) => Number(a.replace("+", "")) - Number(b.replace("+", ""))),
    [],
  );
  const spellCareers = useMemo(() => unique(spells.flatMap((spell) => spell.careers ?? [])), []);
  const skillCategories = useMemo(() => unique(skills.map((skill) => skill.category)), []);
  const tabs = useMemo<TabDefinition[]>(
    () => [{ id: "favorites", label: "Favorites", icon: Star, count: favoriteIds.size }, ...dataTabs],
    [favoriteIds.size],
  );

  const currentEntries = useMemo<ListedEntry[]>(() => {
    const search = query.trim().toLowerCase();
    if (activeTab === "favorites") return favoriteEntries(search);
    const entries = entriesForDataTab(activeTab, search).map((entry) => toListedEntry(activeTab, entry));
    if (!favoriteOnly) return entries;
    return entries.filter((listed) => favoriteIds.has(listed.key));
  }, [
    activeTab,
    query,
    favoriteCategory,
    spellCost,
    spellMode,
    spellCareer,
    itemCategory,
    gameCategory,
    careerType,
    featureType,
    featureTag,
    skillCategory,
    detailedOnly,
    favoriteOnly,
    favoriteIds,
  ]);

  const selected = useMemo(() => {
    if (selectedId) {
      const found = currentEntries.find((listed) => listed.key === selectedId);
      if (found) return found;
    }
    return currentEntries[0] ?? null;
  }, [currentEntries, selectedId]);

  function favoriteEntries(search: string): ListedEntry[] {
    const favoriteTabs = favoriteCategory === "all" ? dataTabs.map((tab) => tab.id) : [favoriteCategory];
    return favoriteTabs
      .flatMap((tab) => entriesForDataTab(tab, search, false).map((entry) => toListedEntry(tab, entry)))
      .filter((listed) => favoriteIds.has(listed.key));
  }

  function entriesForDataTab(tab: DataTabId, search: string, applyFilters = true): AnyEntry[] {
    if (tab === "races") {
      return races.filter((race) => matches(search, [race.name, race.summary, race.archetypes.join(" "), race.traits.join(" "), race.languages]));
    }
    if (tab === "careers") {
      return careers.filter((career) => {
        const typeOk =
          !applyFilters ||
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
    if (tab === "game") {
      return game.filter((card) => {
        const categoryOk = !applyFilters || gameCategory === "all" || card.category === gameCategory;
        return categoryOk && matches(search, [card.title, card.category, card.summary, card.rules.join(" ")]);
      });
    }
    if (tab === "features") {
      return features.filter((feature) => {
        const typeOk = !applyFilters || featureType === "all" || feature.type === featureType;
        const tagOk = !applyFilters || featureTag === "all" || feature.tags.includes(featureTag);
        return (
          typeOk &&
          tagOk &&
          matches(search, [feature.name, feature.type, feature.archetype, feature.prerequisite, feature.description, feature.tags.join(" ")])
        );
      });
    }
    if (tab === "skills") {
      return skills.filter((skill) => {
        const categoryOk = !applyFilters || skillCategory === "all" || skill.category === skillCategory;
        return categoryOk && matches(search, [skill.name, skill.category, skill.governingStat, skill.summary, skill.description, skill.untrained, skill.use]);
      });
    }
    if (tab === "spells") {
      return spells.filter((spell) => {
        const costOk = !applyFilters || spellCost === "all" || spell.cost === spellCost;
        const careerOk = !applyFilters || spellCareer === "all" || (spell.careers ?? []).includes(spellCareer);
        const modeOk =
          !applyFilters ||
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
      const categoryOk = !applyFilters || itemCategory === "all" || item.category === itemCategory;
      const detailOk = !applyFilters || !detailedOnly || Boolean(item.description || item.specialRules);
      return (
        categoryOk &&
        detailOk &&
        matches(search, [item.name, item.category, item.price, item.description, item.specialRules, Object.values(item.fields).join(" ")])
      );
    });
  }

  function switchTab(tab: TabId) {
    setActiveTab(tab);
    setSelectedId(null);
  }

  function toListedEntry(tab: DataTabId, entry: AnyEntry): ListedEntry {
    return { tab, entry, key: entryKey(tab, entry.id) };
  }

  function isFavorite(listed: ListedEntry) {
    return favoriteIds.has(listed.key);
  }

  function toggleFavorite(listed: ListedEntry) {
    const key = listed.key;
    setFavoriteIds((previous) => {
      const next = new Set(previous);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <div className="appShell">
      <aside className="rail">
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

      <main className="workspace">
        <header className="topbar">
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
            <span>{favoriteIds.size} favorites</span>
            <span>{meta.counts.itemDetails} item notes</span>
          </div>
        </header>

        <section className="filters">{renderFilters()}</section>

        <section className="contentGrid">
          <div className="listPane" aria-label="Entry list">
            {currentEntries.map((listed) => {
              const favorite = isFavorite(listed);
              const { entry, tab } = listed;
              return (
                <div key={listed.key} className={selected && listed.key === selected.key ? "entryRow selected" : "entryRow"}>
                  <button className="entrySelect" onClick={() => setSelectedId(listed.key)}>
                    <span>{entryTitle(entry, tab)}</span>
                    <small>
                      {activeTab === "favorites" && <strong>{dataTabLabels[tab]}</strong>}
                      {activeTab === "favorites" && <span aria-hidden="true"> · </span>}
                      {entrySubtitle(entry, tab)}
                    </small>
                  </button>
                  <button
                    className={favorite ? "entryFavoriteButton active" : "entryFavoriteButton"}
                    onClick={() => toggleFavorite(listed)}
                    title={favorite ? "Remove favorite" : "Add favorite"}
                    aria-label={favorite ? "Remove favorite" : "Add favorite"}
                  >
                    <Star size={16} fill={favorite ? "currentColor" : "none"} />
                  </button>
                </div>
              );
            })}
            {currentEntries.length === 0 && <div className="emptyState">No matching entries.</div>}
          </div>

          <article className="detailPane">
            {selected ? (
              <>
                <div className="detailActions">
                  <button className={isFavorite(selected) ? "favoriteAction active" : "favoriteAction"} onClick={() => toggleFavorite(selected)}>
                    <Star size={16} fill={isFavorite(selected) ? "currentColor" : "none"} />
                    <span>{isFavorite(selected) ? "Favorited" : "Add favorite"}</span>
                  </button>
                </div>
                {renderDetail(selected)}
              </>
            ) : (
              <div className="emptyState">Select an entry to start reading.</div>
            )}
          </article>
        </section>
      </main>
    </div>
  );

  function renderFilters() {
    const favoritesToggle = <FavoritesToggle checked={favoriteOnly} onChange={setFavoriteOnly} />;

    if (activeTab === "favorites") {
      return (
        <>
          <label className="filterControl">
            <Star size={16} />
            <select value={favoriteCategory} onChange={(event) => setFavoriteCategory(event.target.value as DataTabId | "all")}>
              <option value="all">All favorite sections</option>
              {dataTabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.label}
                </option>
              ))}
            </select>
          </label>
          <div className="hintLine">
            <Star size={16} fill="currentColor" />
            <span>Saved entries from every section appear here. Use search to narrow the list.</span>
          </div>
        </>
      );
    }

    if (activeTab === "careers") {
      return (
        <>
          <label className="filterControl">
            <Briefcase size={16} />
            <select value={careerType} onChange={(event) => setCareerType(event.target.value)}>
              <option value="all">All careers</option>
              <option value="spellcasting">Spellcasting careers</option>
              <option value="startingOnly">Starting-career only</option>
              <option value="restricted">Restricted second career</option>
            </select>
          </label>
          {favoritesToggle}
        </>
      );
    }
    if (activeTab === "game") {
      return (
        <>
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
          {favoritesToggle}
        </>
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
          {favoritesToggle}
        </>
      );
    }
    if (activeTab === "skills") {
      return (
        <>
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
          {favoritesToggle}
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
          {favoritesToggle}
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
          {favoritesToggle}
        </>
      );
    }
    return (
      <>
        <div className="hintLine">
          <Users size={16} />
          <span>Race data includes starting values, Hero/Veteran/Epic limits, languages, base size, and traits.</span>
        </div>
        {favoritesToggle}
      </>
    );
  }

  function renderDetail(listed: ListedEntry) {
    const { entry, tab } = listed;
    if (tab === "races") return <RaceDetail race={entry as Race} />;
    if (tab === "careers") return <CareerDetail career={entry as Career} />;
    if (tab === "game") return <GameDetail card={entry as CombatCard} />;
    if (tab === "features") return <FeatureDetail feature={entry as Feature} />;
    if (tab === "skills") return <SkillDetail skill={entry as Skill} />;
    if (tab === "spells") return <SpellDetail spell={entry as Spell} />;
    return <ItemDetail item={entry as Item} />;
  }
}

function FavoritesToggle({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="toggleControl favoriteOnlyToggle">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <Star size={15} fill={checked ? "currentColor" : "none"} />
      <span>Favorites only</span>
    </label>
  );
}

function loadFavorites(): Set<string> {
  try {
    const raw = window.localStorage.getItem(FAVORITES_STORAGE_KEY);
    const parsed = JSON.parse(raw ?? "[]");
    return new Set(Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === "string") : []);
  } catch {
    return new Set();
  }
}
