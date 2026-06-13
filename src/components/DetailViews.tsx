import React from "react";
import { BadgeCheck, Boxes, Briefcase, Gamepad2, ListChecks, ScrollText, Sparkles, Users } from "lucide-react";
import type { Career, CombatCard, Feature, Item, Race, Skill, Spell } from "../types";
import { compactRules, fieldLabel, isTextHeading, pageLabel, statOrder, textBlocks } from "../utils";

export function RaceDetail({ race }: { race: Race }) {
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

export function CareerDetail({ career }: { career: Career }) {
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

export function GameDetail({ card }: { card: CombatCard }) {
  return (
    <>
      <DetailHeader icon={<Gamepad2 size={22} />} title={card.title} subtitle={`${card.category} · Core Rules ${pageLabel(card)}`} />
      <p className="lead">{card.summary}</p>
      <RuleList rules={card.rules} />
    </>
  );
}

export function SpellDetail({ spell }: { spell: Spell }) {
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

export function FeatureDetail({ feature }: { feature: Feature }) {
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

export function SkillDetail({ skill }: { skill: Skill }) {
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

export function ItemDetail({ item }: { item: Item }) {
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
