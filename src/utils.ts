import type { AnyEntry, Career, CombatCard, DataTabId, Feature, Item, Race, Skill, Spell } from "./types";

export const statOrder = ["PHY", "SPD", "STR", "AGL", "PRW", "POI", "INT", "ARC", "PER"];

export function normalize(value: unknown): string {
  return String(value ?? "").toLowerCase();
}

export function includesText(value: unknown, query: string): boolean {
  return normalize(value).includes(query);
}

export function matches(query: string, values: unknown[]): boolean {
  if (!query) return true;
  return values.some((value) => includesText(value, query));
}

export function unique(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

export function pageLabel(entry: { bookPage?: number; pageStart?: number; pageEnd?: number }): string {
  const start = entry.pageStart ?? entry.bookPage;
  if (!start) return "";
  const end = entry.pageEnd ?? start;
  return end > start ? `pp. ${start}-${end}` : `p. ${start}`;
}

export function entryTitle(entry: AnyEntry, tab: DataTabId): string {
  if (tab === "game") return (entry as CombatCard).title;
  return (entry as Race | Career | Feature | Skill | Spell | Item).name;
}

export function entrySubtitle(entry: AnyEntry, tab: DataTabId): string {
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
    const label =
      feature.type === "Archetype Benefit"
        ? `${feature.type} · ${feature.archetype}`
        : `${feature.type}${feature.prerequisite ? ` · Prereq: ${feature.prerequisite}` : ""}`;
    return `${label} · ${pageLabel(feature)}`;
  }
  const item = entry as Item;
  return `${item.category} · ${item.price} · ${pageLabel(item)}`;
}

export function entryKey(tab: DataTabId, entryId: string): string {
  return `${tab}:${entryId}`;
}

export function compactRules(values: Array<[string, string]>): string[] {
  return values.filter(([, value]) => Boolean(value)).map(([label, value]) => `${label}: ${value}`);
}

export function fieldLabel(key: string): string {
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function textBlocks(text: string): string[] {
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

export function isTextHeading(block: string): boolean {
  return /:$/.test(block) && block.length < 90;
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
