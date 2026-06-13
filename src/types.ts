export type DataTabId = "races" | "careers" | "game" | "features" | "skills" | "spells" | "items";
export type TabId = "favorites" | DataTabId;

export type Race = {
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

export type CombatCard = {
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

export type Career = {
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

export type Spell = {
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

export type Feature = {
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

export type Skill = {
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

export type Item = {
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

export type AnyEntry = Race | Career | CombatCard | Feature | Skill | Spell | Item;

export type ListedEntry = {
  tab: DataTabId;
  entry: AnyEntry;
  key: string;
};

export type Meta = {
  counts: Record<string, number>;
  source: string;
};
