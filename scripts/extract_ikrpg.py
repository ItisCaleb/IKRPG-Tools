from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PYVENDOR = ROOT / "work" / "pyvendor"
if PYVENDOR.exists():
    sys.path.insert(0, str(PYVENDOR))

from pypdf import PdfReader


STATS = ["PHY", "SPD", "STR", "AGL", "PRW", "POI", "INT", "ARC", "PER"]


CANONICAL_SPELLS = [
    "Arcane Bolt",
    "Arcane Strike",
    "Arcantrik Bolt",
    "Ashen Cloud",
    "Ashes to Ashes",
    "Aura of Protection",
    "Awareness",
    "Banishing Ward",
    "Barrier of Flames",
    "Battering Ram",
    "Batten Down the Hatches",
    "Black Out",
    "Blade of Radiance",
    "Blazing Effigy",
    "Blessing of Health",
    "Blessing of Morrow",
    "Blessings of War",
    "Blizzard",
    "Brittle Frost",
    "Boundless Charge",
    "Broadside",
    "Celerity",
    "Chain Lightning",
    "Chiller",
    "Cleansing Fire",
    "Convection",
    "Crevasse",
    "Crusader's Call",
    "Daylight",
    "Deceleration",
    "Deep Freeze",
    "Earthquake",
    "Earth's Cradle",
    "Earthsplitter",
    "Electrical Blast",
    "Electrify",
    "Eliminator",
    "Entangle",
    "Eyes of Truth",
    "Extinguisher",
    "Fail Safe",
    "Fair Winds",
    "Fire Group",
    "Fire Starter",
    "Flames of Wrath",
    "Flare",
    "Fog of War",
    "Force Field",
    "Force Hammer",
    "Force of Faith",
    "Fortify",
    "Foxhole",
    "Freezing Grip",
    "Freezing Mist",
    "Frozen Ground",
    "Frostbite",
    "Fuel the Flames",
    "Full Throttle",
    "Grind",
    "Guided Blade",
    "Guided Fire",
    "Hand of Fate",
    "Heal",
    "Heightened Reflexes",
    "Hex Blast",
    "Hoarfrost",
    "Howling Flames",
    "Hymn of Battle",
    "Hymn of Passage",
    "Hymn of Shielding",
    "Ice Bolt",
    "Ice Shield",
    "Icy Grip",
    "Ignite",
    "Immolation",
    "Inferno",
    "Influence",
    "Inhospitable Ground",
    "Iron Aggression",
    "Jackhammer",
    "Jump Start",
    "Lamentation",
    "Light in the Darkness",
    "Lightning Tendrils",
    "Locomotion",
    "Mirage",
    "Obliteration",
    "Occultation",
    "Overmind",
    "Polarity Shield",
    "Positive Charge",
    "Power Booster",
    "Prayer of Guidance",
    "Protection from Cold",
    "Protection from Corrosion",
    "Protection from Electricity",
    "Protection from Fire",
    "Purification",
    "Raging Winds",
    "Razor Wind",
    "Redline",
    "Refuge",
    "Return Fire",
    "Rift",
    "Righteous Flames",
    "Rime",
    "Rock Hammer",
    "Rock Wall",
    "Rune Shot: Accuracy",
    "Rune Shot: Black Penny",
    "Rune Shot: Brutal",
    "Rune Shot: Detonator",
    "Rune Shot: Earth Shaker",
    "Rune Shot: Fire Beacon",
    "Rune Shot: Freeze Fire",
    "Rune Shot: Heart Stopper",
    "Rune Shot: Iron Rot",
    "Rune Shot: Molten Shot",
    "Rune Shot: Momentum",
    "Rune Shot: Phantom Seeker",
    "Rune Shot: Shadow Fire",
    "Rune Shot: Silencer",
    "Rune Shot: Spell Cracker",
    "Rune Shot: Spontaneous Combustion",
    "Rune Shot: Thunderbolt",
    "Rune Shot: Trick Shot",
    "Sanguine Blessing",
    "Sea of Fire",
    "Shatter Storm",
    "Shield of Faith",
    "Shock Wave",
    "Short Out",
    "Snipe",
    "Solid Ground",
    "Solovin's Boon",
    "Star Fire",
    "Staying Winter's Hand",
    "Stone Stance",
    "Stone Strength",
    "Storm Tossed",
    "Sunburst",
    "Superiority",
    "Telekinesis",
    "Temper Metal",
    "Tempest",
    "Tide of Steel",
    "Tornado",
    "Transference",
    "Triage",
    "True Path",
    "True Sight",
    "Vision",
    "Voltaic Lock",
    "Wall of Fire",
    "White Out",
    "Wind Blast",
    "Wind Strike",
    "Wings of Air",
    "Winter Storm",
    "Zephyr",
]

SPELL_KEY = {re.sub(r"[^a-z0-9]+", "", spell.lower()): spell for spell in CANONICAL_SPELLS}


def simplify(value: str) -> str:
    value = value.replace("’", "'").replace("`", "'")
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tidy_text(value: str) -> str:
    value = value.replace("\u02dd", '"').replace("˝", '"').replace("´", "'")
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"nathan robertson \(Order #13435911\)", "", value, flags=re.I)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in tidy_text(text).splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if line.lower() in {"magic", "the game", "characters", "gear, mechanika, and alchemy"}:
            continue
        if "nathan robertson" in line.lower():
            continue
        lines.append(line)
    return lines


def read_pdf(pdf_path: Path) -> PdfReader:
    reader = PdfReader(str(pdf_path), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    return reader


def page_text(reader: PdfReader, page_no: int) -> str:
    return reader.pages[page_no - 1].extract_text() or ""


def pages_text(reader: PdfReader, start: int, end: int) -> str:
    return "\n".join(page_text(reader, page_no) for page_no in range(start, end + 1))


def book_page(pdf_page: int) -> int:
    return pdf_page - 1


def page_range(start: int | None, end: int | None = None) -> str:
    if start is None:
        return ""
    if end is None or end == start:
        return f"p. {start}"
    return f"pp. {start}-{end}"


def source_for_pages(start: int | None, end: int | None = None) -> str:
    label = page_range(start, end)
    return f"Core Rules {label}" if label else "Core Rules"


def clean_page_records(reader: PdfReader, start: int, end: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for pdf_page in range(start, end + 1):
        for line in clean_lines(page_text(reader, pdf_page)):
            records.append({"text": line, "pdfPage": pdf_page, "bookPage": book_page(pdf_page)})
    return records


def record_texts(records: list[dict[str, Any]]) -> list[str]:
    return [record["text"] for record in records]


def stat_block(rows: list[tuple[str, Any, Any, Any, Any]]) -> dict[str, dict[str, Any]]:
    return {
        stat: {"start": start, "hero": hero, "veteran": veteran, "epic": epic}
        for stat, start, hero, veteran, epic in rows
    }


def extract_races() -> list[dict[str, Any]]:
    return [
        {
            "id": "human",
            "name": "Human",
            "bookPage": 108,
            "pdfPage": 109,
            "baseSize": "Small",
            "summary": "Adaptable and widespread people with broad career access and an extra starting stat bonus.",
            "archetypes": ["Gifted", "Intellectual", "Mighty", "Skilled"],
            "languages": "Native language plus one other language.",
            "height": "61-75 in male, 55-69 in female",
            "weight": "110-200 lb male, 90-170 lb female",
            "stats": stat_block(
                [
                    ("PHY", 5, 7, 8, 8),
                    ("SPD", 6, 7, 7, 7),
                    ("STR", 4, 6, 7, 8),
                    ("AGL", 3, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 4, 5, 6, 7),
                    ("INT", 3, 5, 6, 7),
                    ("ARC", "*", 4, 6, 8),
                    ("PER", 3, 5, 6, 7),
                ]
            ),
            "traits": [
                "Exceptional Potential: choose +1 PHY, +1 AGL, or +1 INT at character creation before spending Advancement Points.",
            ],
        },
        {
            "id": "dwarf",
            "name": "Dwarf / Rhulfolk",
            "bookPage": 109,
            "pdfPage": 110,
            "baseSize": "Small",
            "summary": "Sturdy, lawful Rhulic craftsmen and soldiers with strong ties to clan and craft.",
            "archetypes": ["Gifted", "Intellectual", "Mighty", "Skilled"],
            "languages": "Rhulic plus one other language.",
            "height": "52-60 in male, 47-55 in female",
            "weight": "150-190 lb male, 105-145 lb female",
            "stats": stat_block(
                [
                    ("PHY", 6, 7, 7, 8),
                    ("SPD", 4, 5, 6, 6),
                    ("STR", 5, 6, 7, 8),
                    ("AGL", 3, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 3, 4, 5, 6),
                    ("INT", 4, 5, 6, 7),
                    ("ARC", "*", 4, 6, 7),
                    ("PER", 3, 4, 6, 7),
                ]
            ),
            "traits": [
                "Load Bearing ability.",
                "Connection (dwarven clan).",
            ],
        },
        {
            "id": "gobber",
            "name": "Gobber",
            "bookPage": 110,
            "pdfPage": 111,
            "baseSize": "Small",
            "summary": "Small, nimble, curious people with a natural knack for alchemy, engineering, and stealth.",
            "archetypes": ["Intellectual", "Mighty", "Skilled"],
            "languages": "Gobberish plus one other language.",
            "height": "34-42 in male, 32-40 in female",
            "weight": "42-60 lb male, 38-55 lb female",
            "stats": stat_block(
                [
                    ("PHY", 4, 6, 7, 7),
                    ("SPD", 6, 7, 7, 7),
                    ("STR", 3, 4, 5, 6),
                    ("AGL", 4, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 3, 5, 6, 7),
                    ("INT", 3, 4, 5, 6),
                    ("ARC", "-", "-", "-", "-"),
                    ("PER", 3, 4, 4, 5),
                ]
            ),
            "traits": [
                "Deft archetype benefit in addition to other archetype benefits.",
                "+1 racial DEF modifier.",
                "Cannot use great weapons or rifles.",
            ],
        },
        {
            "id": "iosan",
            "name": "Iosan",
            "bookPage": 111,
            "pdfPage": 112,
            "baseSize": "Small",
            "summary": "Long-lived and graceful people from secretive Ios, skilled in combat and arcane arts.",
            "archetypes": ["Gifted", "Intellectual", "Mighty", "Skilled"],
            "languages": "Shyr plus one other language.",
            "height": "65-75 in male, 60-70 in female",
            "weight": "125-180 lb male, 85-140 lb female",
            "stats": stat_block(
                [
                    ("PHY", 5, 7, 7, 7),
                    ("SPD", 6, 7, 7, 7),
                    ("STR", 4, 5, 6, 7),
                    ("AGL", 3, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 4, 5, 6, 7),
                    ("INT", 4, 6, 6, 7),
                    ("ARC", "*", 4, 6, 8),
                    ("PER", 3, 5, 6, 7),
                ]
            ),
            "traits": [
                "Begin with one additional ability selected from one of their careers.",
            ],
        },
        {
            "id": "nyss",
            "name": "Nyss",
            "bookPage": 112,
            "pdfPage": 113,
            "baseSize": "Small",
            "summary": "Cold-adapted hunters and warriors from the Shard Spires, now scattered as refugees.",
            "archetypes": ["Gifted", "Mighty", "Skilled"],
            "languages": "Aeric plus one other language.",
            "height": "67-77 in male, 62-72 in female",
            "weight": "140-195 lb male, 95-130 lb female",
            "stats": stat_block(
                [
                    ("PHY", 5, 7, 7, 8),
                    ("SPD", 6, 7, 7, 7),
                    ("STR", 4, 6, 7, 8),
                    ("AGL", 4, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 4, 5, 6, 7),
                    ("INT", 3, 5, 6, 6),
                    ("ARC", "*", 4, 6, 7),
                    ("PER", 3, 5, 6, 6),
                ]
            ),
            "traits": [
                "Gifted Nyss cannot have Arcane Mechanik, Arcanist, Gun Mage, or Warcaster careers.",
                "Nyss bows and Nyss claymores cost 10 gc less during character creation.",
                "+1 on Initiative and PER rolls.",
                "+3 ARM against cold damage.",
                "-3 ARM against fire damage.",
            ],
        },
        {
            "id": "ogrun",
            "name": "Ogrun",
            "bookPage": 113,
            "pdfPage": 114,
            "baseSize": "Medium",
            "summary": "Huge, oath-bound warriors and laborers known for loyalty, strength, and bodyguard traditions.",
            "archetypes": ["Mighty", "Skilled"],
            "languages": "Molgur-Og, Rhulic, plus one other language.",
            "height": "90-105 in male, 82-97 in female",
            "weight": "450-500 lb male, 330-380 lb female",
            "stats": stat_block(
                [
                    ("PHY", 6, 7, 8, 9),
                    ("SPD", 5, 6, 6, 6),
                    ("STR", 6, 8, 9, 10),
                    ("AGL", 3, 5, 5, 6),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 3, 4, 5, 6),
                    ("INT", 3, 5, 5, 6),
                    ("ARC", "-", "-", "-", "-"),
                    ("PER", 2, 4, 5, 6),
                ]
            ),
            "traits": [
                "Huge Stature: can wield a normally two-handed weapon in one hand, suffering -2 on attack rolls with that weapon.",
            ],
        },
        {
            "id": "trollkin",
            "name": "Trollkin",
            "bookPage": 114,
            "pdfPage": 115,
            "baseSize": "Medium",
            "summary": "Hardy, tradition-minded kriel people with tremendous vitality and Dhunian spiritual traditions.",
            "archetypes": ["Gifted", "Mighty", "Skilled"],
            "languages": "Molgur-Trul plus one other language.",
            "height": "71-84 in male, 63-76 in female",
            "weight": "250-330 lb male, 150-230 lb female",
            "stats": stat_block(
                [
                    ("PHY", 6, 8, 9, 10),
                    ("SPD", 5, 6, 6, 6),
                    ("STR", 5, 7, 8, 9),
                    ("AGL", 3, 5, 6, 7),
                    ("PRW", 4, 5, 6, 7),
                    ("POI", 2, 4, 5, 6),
                    ("INT", 3, 4, 5, 6),
                    ("ARC", "*", 4, 6, 7),
                    ("PER", 3, 4, 5, 6),
                ]
            ),
            "traits": [
                "Gifted trollkin cannot have Arcane Mechanik, Arcanist, or Warcaster careers.",
                "Tough archetype benefit in addition to other archetype benefits.",
                "Feat: Revitalize archetype benefit in addition to other archetype benefits.",
            ],
        },
    ]


def maybe_canonical_spell_name(raw: str) -> str | None:
    key = simplify(raw)
    if key in SPELL_KEY:
        return SPELL_KEY[key]
    match = difflib.get_close_matches(key, SPELL_KEY.keys(), n=1, cutoff=0.88)
    if match:
        return SPELL_KEY[match[0]]
    return None


def canonical_spell_name(raw: str) -> str:
    resolved = maybe_canonical_spell_name(raw)
    if resolved:
        return resolved
    return " ".join(part.capitalize() for part in re.sub(r"\s+", " ", raw).strip().split(" "))


SPELL_HEADER = re.compile(
    r"^(?P<name>.+?)\s+(?P<cost>\d\+?|\d+)\s+(?P<rng>self|ctrl|b2b|sp\d+|\d+|[*-])\s+(?P<aoe>ctrl|wall|\d+|[*-])\s+(?P<pow>\d+|[*-])\s+(?P<up>yes|no)\s+(?P<off>yes|no|[*])$",
    re.I,
)
SPELL_LIST_COST = re.compile(r"^COST\s+\d+\s*(?P<names>.*)$", re.I)

SPELL_LIST_GROUP_CAREERS = {
    235: [
        "Arcane Mechanik",
        "Arcane Mechanik",
        "Arcane Mechanik",
        "Arcane Mechanik",
        "Arcanist",
        "Arcanist",
        "Arcanist",
        "Arcanist",
    ],
    236: [
        "Gun Mage",
        "Gun Mage",
        "Gun Mage",
        "Gun Mage",
        "Priest of Menoth",
        "Priest of Menoth",
        "Priest of Menoth",
        "Priest of Menoth",
        "Priest of Morrow",
        "Priest of Morrow",
        "Priest of Morrow",
        "Priest of Morrow",
    ],
    237: [
        "Sorcerer (Fire)",
        "Sorcerer (Fire)",
        "Sorcerer (Fire)",
        "Sorcerer (Fire)",
        "Sorcerer (Ice)",
        "Sorcerer (Ice)",
        "Sorcerer (Ice)",
        "Sorcerer (Ice)",
        "Sorcerer (Stone)",
        "Sorcerer (Stone)",
        "Sorcerer (Stone)",
        "Sorcerer (Stone)",
        "Sorcerer (Storm)",
        "Sorcerer (Storm)",
        "Sorcerer (Storm)",
        "Sorcerer (Storm)",
        "Warcaster",
        "Warcaster",
        "Warcaster",
        "Warcaster",
    ],
}

CAREER_ORDER = [
    "Arcane Mechanik",
    "Arcanist",
    "Gun Mage",
    "Priest of Menoth",
    "Priest of Morrow",
    "Sorcerer (Fire)",
    "Sorcerer (Ice)",
    "Sorcerer (Stone)",
    "Sorcerer (Storm)",
    "Warcaster",
]
CAREER_INDEX = {career: index for index, career in enumerate(CAREER_ORDER)}


def sort_careers(careers: list[str] | set[str]) -> list[str]:
    return sorted(careers, key=lambda career: (CAREER_INDEX.get(career, 999), career))


def extract_spell_list_groups(reader: PdfReader, pdf_page: int) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    current_names: list[str] = []
    current_lines: list[str] = []

    def finish_group() -> None:
        nonlocal current_names, current_lines
        if current_lines:
            groups.append({"names": " ".join(current_names), "lines": current_lines})
        current_names = []
        current_lines = []

    for line in clean_lines(page_text(reader, pdf_page)):
        hit = SPELL_LIST_COST.match(line)
        if hit:
            finish_group()
            current_lines = [line]
            names = hit.group("names").strip()
            current_names = [names] if names else []
            continue
        if current_lines:
            current_lines.append(line)
            current_names.append(line)

    finish_group()
    return groups


def split_spell_list_names(names: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", names).strip(" ,.")
    if not cleaned:
        return []
    return [chunk.strip(" ,.") for chunk in cleaned.split(",") if chunk.strip(" ,.")]


def extract_spell_career_map(reader: PdfReader) -> tuple[dict[str, list[str]], dict[int, set[str]]]:
    career_map: dict[str, set[str]] = {}
    list_lines_by_pdf_page: dict[int, set[str]] = {}

    for pdf_page, careers in SPELL_LIST_GROUP_CAREERS.items():
        groups = extract_spell_list_groups(reader, pdf_page)
        for group, career in zip(groups, careers):
            list_lines_by_pdf_page.setdefault(pdf_page, set()).update(group["lines"])
            for raw_name in split_spell_list_names(group["names"]):
                spell_name = maybe_canonical_spell_name(raw_name)
                if spell_name:
                    career_map.setdefault(spell_name, set()).add(career)

    return {spell: sort_careers(careers) for spell, careers in career_map.items()}, list_lines_by_pdf_page


def normalize_stat(value: str) -> str:
    value = value.replace("-", "—")
    if value.lower().startswith("sp"):
        return "SP " + value[2:]
    if value.lower() == "ctrl":
        return "CTRL"
    if value.lower() == "self":
        return "Self"
    if value.lower() == "b2b":
        return "B2B"
    if value.lower() == "wall":
        return "Wall"
    return value


def extract_spells(reader: PdfReader) -> list[dict[str, Any]]:
    spell_careers, spell_list_lines_by_pdf_page = extract_spell_career_map(reader)
    records = clean_page_records(reader, 237, 246)
    lines = record_texts(records)
    spells: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    description: list[dict[str, Any]] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        text = " ".join(record["text"] for record in description)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\bCOST RNG AOE POW UP OFF\b", "", text, flags=re.I).strip()
        page_end = description[-1]["bookPage"] if description else current["pageStart"]
        current["description"] = text
        current["pageEnd"] = page_end
        current["pdfPageEnd"] = description[-1]["pdfPage"] if description else current["pdfPageStart"]
        current["source"] = source_for_pages(current["pageStart"], page_end)
        current["tags"] = spell_tags(current, text)
        spells.append(current)
        current = None
        description = []

    index = 0
    while index < len(lines):
        line = lines[index]
        pdf_page = records[index]["pdfPage"]
        if line in spell_list_lines_by_pdf_page.get(pdf_page, set()):
            index += 1
            continue
        if re.match(r"^(COST|Fire$|iCe$|stoNe$|Storm$|SORCERER SPELLS|WARCASTER SPELLS|spell desCriptions|aniM i)", line, re.I):
            index += 1
            continue
        matched = None
        consumed = 1
        canonical_name = None
        for span in (1, 2, 3):
            candidate = " ".join(lines[index : index + span])
            candidate = candidate.replace("—", "-").replace("–", "-")
            hit = SPELL_HEADER.match(candidate)
            if hit and (canonical_name := maybe_canonical_spell_name(hit.group("name"))):
                matched = hit
                consumed = span
                break
        if matched:
            finalize()
            raw_name = matched.group("name")
            spell_name = canonical_name or canonical_spell_name(raw_name)
            current = {
                "id": simplify(raw_name),
                "name": spell_name,
                "rawName": raw_name,
                "cost": matched.group("cost"),
                "range": normalize_stat(matched.group("rng")),
                "aoe": normalize_stat(matched.group("aoe")),
                "pow": normalize_stat(matched.group("pow")),
                "upkeep": matched.group("up").lower() == "yes",
                "offensive": matched.group("off").lower() == "yes",
                "offensiveMode": normalize_stat(matched.group("off")),
                "careers": spell_careers.get(spell_name, []),
                "bookPage": records[index]["bookPage"],
                "pageStart": records[index]["bookPage"],
                "pageEnd": records[index]["bookPage"],
                "pdfPageStart": records[index]["pdfPage"],
                "pdfPageEnd": records[index]["pdfPage"],
                "source": source_for_pages(records[index]["bookPage"]),
            }
            index += consumed
            continue
        if current:
            description.append(records[index])
        index += 1
    finalize()

    seen: dict[str, dict[str, Any]] = {}
    for spell in spells:
        seen[spell["name"]] = spell
    return sorted(seen.values(), key=lambda item: item["name"])


def spell_tags(spell: dict[str, Any], text: str) -> list[str]:
    tags = []
    haystack = " ".join([spell["name"], text]).lower()
    for tag, terms in {
        "damage": ["damage roll", "pow"],
        "fire": ["fire"],
        "cold": ["cold", "ice", "frost"],
        "electricity": ["electric", "lightning", "storm"],
        "defense": ["arm", "def", "cover", "concealment", "cannot be targeted"],
        "movement": ["move", "advance", "charge", "push", "slam", "place"],
        "steamjack": ["steamjack", "battlegroup", "focus"],
        "control": ["control area", "ctrl"],
        "rune shot": ["rune shot"],
        "healing": ["heal", "medicine", "vitality", "stabilized"],
    }.items():
        if any(term in haystack for term in terms):
            tags.append(tag)
    if spell["upkeep"]:
        tags.append("upkeep")
    if spell["offensive"]:
        tags.append("offensive")
    return sorted(set(tags))


PRICE_CATEGORIES = [
    "Light Armor",
    "Medium Armor",
    "Heavy Armor",
    "Melee Weapons",
    "Ranged Weapons",
    "Ammunition and Ranged Weapon Accessories",
    "Clothing",
    "Equipment",
    "Mounts and Riding Equipment",
    "Food, Drink, and Lodging",
    "Mechanika",
    "Mechanika Runes",
    "Mechanikal Devices",
    "Alchemical Ingredients (per unit)",
    "Alchemical Compounds",
    "Alchemical Weapons",
]

PRICE_CATEGORY_KEYS = {simplify(category): category for category in PRICE_CATEGORIES}
PRICE_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<price>\+?\d[\d,]*\+?\s*gc\+?|\d[\d,]*\+\s*gc|\d[\d,]*\s*gc(?:\s*each)?|\d[\d,]*)$",
    re.I,
)


def extract_price_list(reader: PdfReader) -> list[dict[str, Any]]:
    records = clean_page_records(reader, 248, 252)
    items: list[dict[str, Any]] = []
    category: str | None = None
    buffer = ""
    buffer_record: dict[str, Any] | None = None

    for record in records:
        line = record["text"]
        if line.upper() == "ARMOR":
            break
        key = simplify(line)
        if key in PRICE_CATEGORY_KEYS:
            category = PRICE_CATEGORY_KEYS[key]
            buffer = ""
            buffer_record = None
            continue
        if category is None or line.lower().startswith("price lists"):
            continue
        candidate = f"{buffer} {line}".strip() if buffer else line
        start_record = buffer_record or record
        match = PRICE_RE.match(candidate)
        if match:
            name = normalize_item_name(match.group("name"))
            page_start = start_record["bookPage"]
            page_end = record["bookPage"]
            items.append(
                {
                    "id": f"{simplify(category)}-{simplify(name)}",
                    "name": name,
                    "category": category,
                    "price": normalize_price(match.group("price")),
                    "bookPage": page_start,
                    "pageStart": page_start,
                    "pageEnd": page_end,
                    "pdfPageStart": start_record["pdfPage"],
                    "pdfPageEnd": record["pdfPage"],
                    "source": f"{source_for_pages(page_start, page_end)} price list",
                }
            )
            buffer = ""
            buffer_record = None
        else:
            sentence_like = len(line) > 90 or bool(re.search(r"[.!?]\s*$", line))
            if sentence_like:
                buffer = ""
                buffer_record = None
            else:
                buffer = candidate
                buffer_record = start_record
    return items


def normalize_price(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if re.fullmatch(r"\d+", value):
        return value + " gc"
    return value


def normalize_item_name(value: str) -> str:
    value = value.replace("’", "'").replace("`", "'")
    value = re.sub(r"\s+", " ", value).strip()
    replacements = {
        "tW o": "two",
        "Co Mbat": "combat",
        "b attle": "battle",
        "sM oKe": "smoke",
        "aMM o": "ammo",
        "MeChaniK": "mechanik",
        "WrenCh": "wrench",
        "Ja CK": "jack",
        "t ool": "tool",
        "WorKshop": "workshop",
        "CloCK": "clock",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    if value.isupper():
        return value.title()
    return " ".join(part[:1].upper() + part[1:] for part in value.split(" "))


FIELD_RE = re.compile(
    r"^(Cost|Skill|Attack Modifier|POW|Ammo|Effective Range|Extreme Range|AOE|SPD Modifier|DEF Modifier|ARM Modifier|"
    r"Type|Location|Power Output|Lifespan|Rune Points|Brewing Requirements|Ingredients|Total Material Cost|"
    r"Fabrication Requirements|Material Costs?|Height/Weight|Fuel Burn/Load Usage|Initial Service Date|"
    r"Original Chassis Design|Stock Cortex):\s*(.+)$",
    re.I,
)

DETAIL_SECTION_RE = re.compile(
    r"^(Description|Special Rules|Effect|Alchemical Formula|Fabrication Rules|Fabrication)(?:\s*:\s*(.*)|\s*)$",
    re.I,
)


def item_aliases(item: dict[str, Any]) -> set[str]:
    name = item["name"]
    category = item["category"]
    aliases = {simplify(name)}

    without_parenthetical = re.sub(r"\([^)]*\)", "", name).strip()
    aliases.add(simplify(without_parenthetical))

    before_colon = re.split(r"\s*:\s*", name, 1)[0].strip()
    aliases.add(simplify(before_colon))

    if category in {"Food, Drink, and Lodging", "Ammunition and Ranged Weapon Accessories"}:
        aliases.add(simplify(name.split(",", 1)[0]))

    if category == "Alchemical Weapons" and "alchemical grenade" in name.lower():
        aliases.add(simplify("Alchemical Grenade"))

    if name.lower().startswith("firearm ammunition"):
        aliases.add(simplify("Firearm Ammunition"))
    if name.lower().startswith("arrows or bolts"):
        aliases.add(simplify("Arrows or Bolts"))
    if name.lower().startswith("artillery ammunition"):
        aliases.add(simplify("Artillery Rounds"))
    if name.lower().startswith("alchemical acid"):
        aliases.add(simplify("Alchemical Acid"))
    if name.lower().startswith("bottled light"):
        aliases.add(simplify("Bottled Light"))
    if name == "Alchemist's Stone":
        aliases.add(simplify("Alchemical Stone"))

    return {alias for alias in aliases if alias}


def build_item_alias_map(price_items: list[dict[str, Any]]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for item in price_items:
        for alias in item_aliases(item):
            aliases.setdefault(alias, [])
            if item["name"] not in aliases[alias]:
                aliases[alias].append(item["name"])
    return aliases


def extract_item_details(reader: PdfReader, price_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    aliases = build_item_alias_map(price_items)
    records = split_inline_item_heading_records(clean_page_records(reader, 252, 299), aliases)
    details: dict[str, dict[str, Any]] = {}
    index = 0

    while index < len(records):
        line = records[index]["text"]
        key = simplify(line)
        if is_item_heading_line(line) and key in aliases and has_detail_marker(record_texts(records), index):
            item_names = aliases[key]
            block: list[dict[str, Any]] = [records[index]]
            index += 1
            while index < len(records):
                next_line = records[index]["text"]
                next_key = simplify(next_line)
                if is_item_heading_line(next_line) and next_key in aliases and has_detail_marker(record_texts(records), index):
                    break
                if is_item_section_heading(next_line):
                    break
                block.append(records[index])
                index += 1
            parsed = parse_item_block(record_texts(block))
            page_start = block[0]["bookPage"]
            page_end = block[-1]["bookPage"]
            parsed.update(
                {
                    "bookPage": page_start,
                    "pageStart": page_start,
                    "pageEnd": page_end,
                    "pdfPageStart": block[0]["pdfPage"],
                    "pdfPageEnd": block[-1]["pdfPage"],
                    "source": source_for_pages(page_start, page_end),
                }
            )
            for item_name in item_names:
                details[simplify(item_name)] = parsed
            continue
        index += 1
    return details


ITEM_SECTION_HEADINGS = {
    simplify(heading)
    for heading in [
        "Light Armor",
        "Medium Armor",
        "Heavy Armor",
        "Melee Weapons",
        "Ranged Weapons",
        "Ammunition and Ranged Weapon Accessories",
        "Clothing",
        "Equipment",
        "Mounts and Riding Equipment",
        "Food, Drink, and Lodging",
        "Mechanika",
        "Capacitors",
        "Runeplates",
        "Mechanika Runes",
        "Mechanikal Devices",
        "Warcaster Armor",
        "Alchemy",
        "Primary Alchemical Ingredients",
        "Alchemical Items",
        "Field Alchemy",
        "Grenades",
        "Alternative Methods of Delivery",
        "Armor",
    ]
}


def split_inline_item_heading_records(records: list[dict[str, Any]], aliases: dict[str, list[str]]) -> list[dict[str, Any]]:
    split_records: list[dict[str, Any]] = []
    for record in records:
        line = record["text"]
        if "." in line:
            prefix, suffix = line.rsplit(".", 1)
            suffix = suffix.strip()
            if simplify(suffix) in aliases:
                if prefix.strip():
                    split_records.append({**record, "text": prefix.strip() + "."})
                split_records.append({**record, "text": suffix})
                continue
        split_records.append(record)
    return split_records


def split_inline_item_headings(lines: list[str], aliases: dict[str, list[str]]) -> list[str]:
    split_lines: list[str] = []
    for line in lines:
        if "." in line:
            prefix, suffix = line.rsplit(".", 1)
            suffix = suffix.strip()
            if simplify(suffix) in aliases:
                if prefix.strip():
                    split_lines.append(prefix.strip() + ".")
                split_lines.append(suffix)
                continue
        split_lines.append(line)
    return split_lines


def is_item_heading_line(line: str) -> bool:
    if re.search(r"[.!?]\s*$", line):
        return False
    if len(line) > 90:
        return False
    return True


def is_item_section_heading(line: str) -> bool:
    key = simplify(line)
    if key in ITEM_SECTION_HEADINGS:
        return True
    return (
        line.isupper()
        and ":" not in line
        and len(line) > 4
        and not re.match(r"^(PHY|STR|SPD|AGL|PRW|POI|INT|PER|MAT|RAT|DEF|ARM)\b", line)
    )


def has_detail_marker(lines: list[str], index: int) -> bool:
    lookahead = lines[index + 1 : index + 9]
    return any(
        next_line.lower().startswith(("cost:", "description:", "type:", "phy ", "rune points:", "ammo:", "effect:"))
        for next_line in lookahead
    )


def parse_item_block(block: list[str]) -> dict[str, Any]:
    fields: dict[str, str] = {}
    description: list[str] = []
    special: list[str] = []
    section = "preamble"

    for line in block[1:]:
        hit = FIELD_RE.match(line)
        if hit:
            field_name = hit.group(1).lower()
            fields[field_name.replace(" ", "_")] = hit.group(2).strip()
            section = "description" if field_name == "cost" else ""
            continue

        section_hit = DETAIL_SECTION_RE.match(line)
        if section_hit:
            label = section_hit.group(1).lower()
            rest = (section_hit.group(2) or "").strip()
            section = "description" if label == "description" else "special"
            if rest:
                (description if section == "description" else special).append(rest)
            continue

        if section == "description":
            description.append(line)
        elif section == "special":
            special.append(line)
        elif section == "preamble":
            description.append(line)

    return {
        "fields": fields,
        "description": re.sub(r"\s+", " ", " ".join(description)).strip(),
        "specialRules": re.sub(r"\s+", " ", " ".join(special)).strip(),
        "source": "Core Rules gear chapter pp. 251-298; price lists pp. 247-251",
    }


def manual_item_details() -> dict[str, dict[str, Any]]:
    return {
        simplify("Sword-cannon, Heavy"): {
            "bookPage": 270,
            "pageStart": 270,
            "pageEnd": 271,
            "pdfPageStart": 271,
            "pdfPageEnd": 272,
            "fields": {
                "ammo": "1 (heavy round)",
                "effective_range": '60 feet (10")',
                "extreme_range": "300 feet",
                "skill": "Rifle",
                "attack_modifier": "-1",
                "pow": "12",
                "aoe": "-",
            },
            "description": "This weapon integrates a heavy, single-shot rifle with the blade of a sword.",
            "specialRules": (
                "When used as a melee weapon, this weapon has an attack modifier of -1, is POW 3, and uses the "
                "One-Handed Weapon skill. It costs 3 gc for blasting powder, bullets, and casings for five heavy rounds. "
                "As part of a charge, after moving but before making the charge attack, a character can spend 1 feat "
                "point to make one ranged attack with this weapon targeting the enemy charged unless the character was "
                "in melee with the enemy at the start of his turn."
            ),
            "source": source_for_pages(270, 271),
        },
        simplify("Runeplate, Blank"): {
            "bookPage": 284,
            "pageStart": 284,
            "pageEnd": 284,
            "pdfPageStart": 285,
            "pdfPageEnd": 285,
            "fields": {"cost": "10 gc"},
            "description": (
                "Runeplates are rare, magically attuned surfaces used to hold mechanika runes. A blank runeplate can "
                "later be inscribed with runes of one type, up to its rune point allowance."
            ),
            "specialRules": "All runes on a single runeplate must be of the same type.",
            "source": source_for_pages(284),
        },
        simplify("Blast Arrow, Empty"): {
            "bookPage": 297,
            "pageStart": 297,
            "pageEnd": 297,
            "pdfPageStart": 298,
            "pdfPageEnd": 298,
            "fields": {"cost": "10 gc"},
            "description": "An empty blast arrow vessel is a heavy arrow fitted with an alchemical warhead housing.",
            "specialRules": (
                "A blast arrow uses the bow's RNG, has a 3-inch AOE, and has a -1 attack modifier. Its effect depends "
                "on the alchemical compound loaded into the warhead."
            ),
            "source": source_for_pages(297),
        },
        simplify("Rifle Grenade, Empty"): {
            "bookPage": 297,
            "pageStart": 297,
            "pageEnd": 297,
            "pdfPageStart": 298,
            "pdfPageEnd": 298,
            "fields": {"cost": "10 gc"},
            "description": "An empty rifle grenade vessel is a rifle-fired delivery housing for alchemical compounds.",
            "specialRules": (
                "A rifle grenade is loaded onto a military rifle as a quick action. When fired, it has a range of "
                "60 feet, no extreme range, and uses the AOE and effects of the loaded grenade type."
            ),
            "source": source_for_pages(297),
        },
    }


def merge_items(price_items: list[dict[str, Any]], details: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for item in price_items:
        detail = details.get(simplify(item["name"]))
        if detail:
            item = {**item, **detail}
            item["id"] = f"{simplify(item['category'])}-{simplify(item['name'])}"
        else:
            item = {**item, "fields": {}, "description": "", "specialRules": ""}
        merged.append(item)
    return merged


def canonical_clean_title(value: str) -> str:
    value = value.replace("’", "'").replace("`", "'")
    value = value.replace("'Ja CK", "'Jack")
    value = value.replace("T une", "Tune").replace("T wo", "Two")
    value = re.sub(r"\([^)]*\)\*?", "", value)
    value = value.replace("*", "")
    value = re.sub(r"\s+", " ", value).strip()
    if value.lower().startswith("feat:"):
        return "Feat: " + canonical_clean_title(value.split(":", 1)[1])
    title = " ".join(part[:1].upper() + part[1:].lower() for part in value.split(" "))
    title = title.replace("'jack", "'Jack")
    title = title.replace("-weapon", "-Weapon").replace("-by", "-By")
    for word in ("Of", "To", "In", "The"):
        title = re.sub(rf"(?<!^)\b{word}\b", word.lower(), title)
    title = title.replace(": to ", ": To ").replace(": the ", ": The ")
    return title


def archetype_heading(line: str) -> str | None:
    key = simplify(line)
    return {
        "gifted": "Gifted",
        "intellectual": "Intellectual",
        "mighty": "Mighty",
        "skilled": "Skilled",
    }.get(key)


def parse_named_dash_entry(line: str) -> tuple[str, str]:
    text = line.lstrip("• ").strip()
    match = re.match(r"(.+?)\s+-\s+(.+)", text)
    if not match:
        return canonical_clean_title(text), ""
    return canonical_clean_title(match.group(1)), match.group(2).strip()


def extract_benefits(reader: PdfReader) -> list[dict[str, Any]]:
    records = clean_page_records(reader, 116, 118)
    benefits: list[dict[str, Any]] = []
    current_archetype: str | None = None
    current: dict[str, Any] | None = None
    description: list[dict[str, Any]] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        current["description"] = re.sub(r"\s+", " ", " ".join(record["text"] for record in description)).strip()
        page_end = description[-1]["bookPage"] if description else current["pageStart"]
        current["pageEnd"] = page_end
        current["pdfPageEnd"] = description[-1]["pdfPage"] if description else current["pdfPageStart"]
        current["source"] = source_for_pages(current["pageStart"], page_end)
        current["tags"] = classify_rules_text(current["name"] + " " + current["description"])
        benefits.append(current)
        current = None
        description = []

    for record in records:
        line = record["text"]
        heading = archetype_heading(line)
        if heading:
            finalize()
            current_archetype = heading
            continue
        if line.startswith("STEP 3:"):
            finalize()
            break
        if not current_archetype:
            continue
        if line.startswith("•"):
            finalize()
            name, rest = parse_named_dash_entry(line)
            current = {
                "id": f"{simplify(current_archetype)}-{simplify(name)}",
                "name": name,
                "type": "Archetype Benefit",
                "archetype": current_archetype,
                "bookPage": record["bookPage"],
                "pageStart": record["bookPage"],
                "pageEnd": record["bookPage"],
                "pdfPageStart": record["pdfPage"],
                "pdfPageEnd": record["pdfPage"],
                "source": source_for_pages(record["bookPage"]),
            }
            if rest:
                description.append({**record, "text": rest})
        elif current:
            description.append(record)
    finalize()
    return benefits


def ability_name_map(reader: PdfReader) -> dict[str, str]:
    lines = clean_lines(page_text(reader, 157))
    names: list[str] = []
    for line in lines[2:]:
        if line.startswith("nathan"):
            break
        names.append(canonical_clean_title(line))
    names.append("Disease Resistance")
    return {simplify(name): name for name in names}


def canonical_ability_name(raw: str, names: dict[str, str]) -> str:
    key = simplify(raw)
    if key in names:
        return names[key]
    match = difflib.get_close_matches(key, names.keys(), n=1, cutoff=0.85)
    if match:
        return names[match[0]]
    return canonical_clean_title(raw)


def parse_prerequisite(line: str) -> str:
    return re.sub(r"^Prerequisite\s*:?\s*", "", line, flags=re.I).strip() or "None"


def extract_abilities(reader: PdfReader) -> list[dict[str, Any]]:
    names = ability_name_map(reader)
    records = clean_page_records(reader, 158, 169)
    lines = record_texts(records)
    abilities: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    description: list[dict[str, Any]] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        current["description"] = re.sub(r"\s+", " ", " ".join(record["text"] for record in description)).strip()
        page_end = description[-1]["bookPage"] if description else current["pageStart"]
        current["pageEnd"] = page_end
        current["pdfPageEnd"] = description[-1]["pdfPage"] if description else current["pdfPageStart"]
        current["source"] = source_for_pages(current["pageStart"], page_end)
        current["tags"] = classify_rules_text(
            current["name"] + " " + current.get("prerequisite", "") + " " + current["description"]
        )
        abilities.append(current)
        current = None
        description = []

    for index, line in enumerate(lines):
        if line.lower().startswith("prerequisite") and index > 0:
            finalize()
            raw_name = lines[index - 1]
            name = canonical_ability_name(raw_name, names)
            current = {
                "id": simplify(name),
                "name": name,
                "type": "Ability",
                "prerequisite": parse_prerequisite(line),
                "bookPage": records[index - 1]["bookPage"],
                "pageStart": records[index - 1]["bookPage"],
                "pageEnd": records[index]["bookPage"],
                "pdfPageStart": records[index - 1]["pdfPage"],
                "pdfPageEnd": records[index]["pdfPage"],
                "source": source_for_pages(records[index - 1]["bookPage"], records[index]["bookPage"]),
            }
            continue
        if current:
            key = simplify(line)
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if key in names and next_line.lower().startswith("prerequisite"):
                continue
            if line.lower().startswith("connections"):
                finalize()
                break
            description.append(records[index])
    finalize()

    deduped: dict[str, dict[str, Any]] = {}
    for ability in abilities:
        deduped[ability["id"]] = ability
    return sorted(deduped.values(), key=lambda item: item["name"])


def classify_rules_text(value: str) -> list[str]:
    haystack = value.lower()
    tags = []
    for tag, terms in {
        "feat": ["feat point", "feat:"],
        "combat": ["attack", "damage", "melee", "ranged", "charge", "slam"],
        "magic": ["spell", "arc", "magic", "rune", "focus"],
        "movement": ["advance", "move", "movement", "pathfinder", "rough terrain"],
        "defense": ["arm", "def", "cover", "concealment", "shield", "knocked down"],
        "skill": ["skill", "rolls are boosted", "reroll failed"],
        "command": ["command range", "battle plan", "friendly character"],
        "steamjack": ["steamjack", "'jack", "cortex", "battlegroup"],
        "social": ["social", "etiquette", "bribery", "deception", "noble"],
    }.items():
        if any(term in haystack for term in terms):
            tags.append(tag)
    return sorted(set(tags))


CAREER_PAGES = [
    ("Alchemist", 121),
    ("Arcane Mechanik", 122),
    ("Arcanist", 123),
    ("Aristocrat", 124),
    ("Bounty Hunter", 125),
    ("Cutthroat", 126),
    ("Duelist", 127),
    ("Explorer", 128),
    ("Fell Caller", 129),
    ("Field Mechanik", 130),
    ("Gun Mage", 131),
    ("Highwayman", 132),
    ("Investigator", 133),
    ("Iron Fang", 134),
    ("Knight", 135),
    ("Mage Hunter", 136),
    ("Man-at-Arms", 137),
    ("Military Officer", 138),
    ("Pirate", 139),
    ("Pistoleer", 140),
    ("Priest", 141),
    ("Ranger", 142),
    ("Rifleman", 143),
    ("Soldier", 144),
    ("Sorcerer", 145),
    ("Spy", 146),
    ("Stormblade", 147),
    ("Thief", 148),
    ("Trencher", 149),
    ("Warcaster", 150),
]

CAREER_FIELD_LABELS = [
    "Abilities",
    "Connections",
    "Military Skills",
    "Occupational Skills",
    "Spells",
    "Special",
]


def cleaned_joined_lines(lines: list[str]) -> str:
    text = " ".join(lines)
    text = text.replace(" ,", ",").replace(" .", ".")
    return re.sub(r"\s+", " ", text).strip()


def career_marker(name: str, label: str) -> re.Pattern[str]:
    words = [re.escape(part) for part in name.split()]
    label_words = [re.escape(part) for part in label.split()]
    return re.compile(
        r"\b" + r"\s+".join(words) + r"\s+" + r"\s+".join(label_words) + r"\b",
        re.I,
    )


def extract_label_value(text: str, label: str, stop_labels: list[str]) -> str:
    stop = "|".join(re.escape(item) for item in stop_labels)
    match = re.search(rf"\b{re.escape(label)}\s*:\s*(.*?)(?=\b(?:{stop})\s*:|$)", text, re.I)
    return re.sub(r"\s+", " ", match.group(1)).strip(" .") if match else ""


def extract_starting_fields(text: str, name: str) -> dict[str, str]:
    start_match = re.search(r"Starting\s+abilitieS.*?(?=\b(?:Abilities|Connections|Military Skills|Occupational Skills|Spells|Special)\s*:)", text, re.I)
    assets_match = re.search(r"Starting\s+aSSetS\b", text, re.I)
    start_index = start_match.end() if start_match else 0
    assets_index = assets_match.start() if assets_match else len(text)
    block = text[start_index:assets_index]

    if name == "Sorcerer":
        special_match = re.search(r"\bSpecial\s*:\s*(.*?)(?=\bMilitary Skills\s*:)", block, re.I)
        return {
            "abilities": "",
            "connections": "",
            "militarySkills": extract_label_value(block, "Military Skills", CAREER_FIELD_LABELS),
            "occupationalSkills": extract_label_value(block, "Occupational Skills", CAREER_FIELD_LABELS),
            "spells": "Choose Fire, Ice, Stone, or Storm starting spells from the Sorcerer element rules.",
            "special": re.sub(r"\s+", " ", special_match.group(1)).strip(" .") if special_match else "",
            "notes": re.sub(r"\s+", " ", block).strip(" ."),
        }

    return {
        "abilities": extract_label_value(block, "Abilities", CAREER_FIELD_LABELS),
        "connections": extract_label_value(block, "Connections", CAREER_FIELD_LABELS),
        "militarySkills": extract_label_value(block, "Military Skills", CAREER_FIELD_LABELS),
        "occupationalSkills": extract_label_value(block, "Occupational Skills", CAREER_FIELD_LABELS),
        "spells": extract_label_value(block, "Spells", CAREER_FIELD_LABELS),
        "special": extract_label_value(block, "Special", CAREER_FIELD_LABELS),
        "notes": re.sub(r"\s+", " ", block).strip(" ."),
    }


def extract_starting_assets(text: str, name: str) -> str:
    assets = re.search(r"Starting\s+aSSetS\b(.*)", text, re.I)
    if not assets:
        return ""
    tail = assets.group(1)
    stops = [
        career_marker(name, "Abilities"),
        career_marker(name, "Connection"),
        career_marker(name, "Connections"),
        career_marker(name, "Military Skills"),
        career_marker(name, "Occupational Skills"),
        career_marker(name, "Spells"),
    ]
    stop_positions = [match.start() for pattern in stops if (match := pattern.search(tail))]
    end = min(stop_positions) if stop_positions else len(tail)
    return re.sub(r"\s+", " ", tail[:end]).strip(" .")


def progression_field_key(label: str) -> str:
    key = simplify(label)
    if key.startswith("abil"):
        return "abilities"
    if key.startswith("connect"):
        return "connections"
    if key.startswith("military"):
        return "militarySkills"
    if key.startswith("occupational"):
        return "occupationalSkills"
    return "spells"


def clean_progression_value(value: str) -> str:
    value = re.split(
        r"\b(?:Experienced|Playing an?|The experienced|The character is|A character is|It is not uncommon|Where there)\b",
        value,
        maxsplit=1,
        flags=re.I,
    )[0]
    value = value.replace(" ,", ",").replace(" -", " —")
    value = re.sub(r"\s+", " ", value).strip(" .")
    if value == "-":
        return "—"
    return value


def extract_career_progression(text: str, name: str) -> dict[str, str]:
    result = {"abilities": "", "connections": "", "militarySkills": "", "occupationalSkills": "", "spells": ""}
    name_pattern = r"\b" + r"\s+".join(re.escape(part) for part in name.split()) + r"\s+"
    label_pattern = r"(?P<label>abilities|connections?|military\s+skills|occupational\s+skills|spells)"
    markers = list(re.finditer(name_pattern + label_pattern, text, re.I))

    for index, marker in enumerate(markers):
        field = progression_field_key(marker.group("label"))
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        result[field] = clean_progression_value(text[start:end])

    return result


def extract_career_summary(text: str, name: str) -> str:
    compact = re.sub(r"\s+", " ", text)
    playing = re.search(rf"Playing an? {re.escape(name)}\s*:\s*(.*?)(?=Starting abilitieS|Experienced|$)", compact, re.I)
    if playing:
        return re.sub(r"\s+", " ", playing.group(1)).strip()[:700].rsplit(".", 1)[0] + "."
    lead = re.search(rf"\b(?:The|An?|This) [^.]*\b{re.escape(name.split()[0])}\b.*?\.", compact, re.I)
    if lead:
        return re.sub(r"\s+", " ", lead.group(0)).strip()
    return ""


def normalize_prerequisite(value: str) -> str:
    value = re.sub(r"\bStarting\s+Career\b", "Starting career", value, flags=re.I)
    value = value.replace("HuMAN", "Human").replace("FOCuSER", "Focuser").replace("OGRuN", "Ogrun")
    value = value.replace("TROLLKIN", "Trollkin").replace("GIFTED", "Gifted").replace("IOSAN", "Iosan")
    value = value.replace("KHADORAN", "Khadoran").replace("CYGNARAN", "Cygnaran")
    value = value.replace("RESTRICTED 2ND CAREER", "Restricted second career")
    value = value.replace("TRADITION", "Tradition")
    value = value.replace("NONE", "None")
    value = re.sub(r"\bAND\b", "and", value)
    value = re.sub(r"\bOR\b", "or", value)
    return re.sub(r"\s+", " ", value).strip(" ,.")


def clean_prerequisite(lines: list[str]) -> str:
    parts: list[str] = []
    capture = False
    for line in lines:
        if not capture and re.search(r"PRER\w+\s*:", line, re.I):
            capture = True
            parts.append(re.sub(r"^.*?PRER\w+\s*:\s*", "", line, flags=re.I))
            continue
        if capture:
            if simplify(line).startswith("startingabilities") or simplify(line).startswith("startingassets"):
                break
            if re.search(r"\b(STARTING CAREER|RESTRICTED|CAREER|AND|OR)\b", line):
                parts.append(line)
                continue
            break
    if not parts:
        return "None"
    return normalize_prerequisite(" ".join(parts))


def extract_careers(reader: PdfReader) -> list[dict[str, Any]]:
    careers: list[dict[str, Any]] = []

    for name, pdf_page in CAREER_PAGES:
        records = clean_page_records(reader, pdf_page, pdf_page)
        lines = record_texts(records)
        text = cleaned_joined_lines(lines)
        book = book_page(pdf_page)
        starting = extract_starting_fields(text, name)
        progression = extract_career_progression(text, name)
        prerequisites = clean_prerequisite(lines)
        careers.append(
            {
                "id": simplify(name),
                "name": name,
                "prerequisites": prerequisites,
                "startingOnly": "starting career" in prerequisites.lower(),
                "restrictedSecondCareer": "restricted second career" in prerequisites.lower(),
                "spellcasting": bool(starting["spells"] or progression["spells"]),
                "summary": extract_career_summary(text, name),
                "starting": {
                    **starting,
                    "assets": extract_starting_assets(text, name),
                },
                "progression": progression,
                "bookPage": book,
                "pageStart": book,
                "pageEnd": book,
                "pdfPageStart": pdf_page,
                "pdfPageEnd": pdf_page,
                "source": source_for_pages(book),
            }
        )

    return careers


MILITARY_SKILLS = [
    ("Archery", "Poise", "Each level adds to POI when making attacks with bows."),
    ("Crossbow", "Poise", "Each level adds to POI when making attacks with crossbows."),
    ("Great Weapon", "Prowess", "Each level adds to PRW when making attacks with great weapons."),
    ("Hand Weapon", "Prowess", "Each level adds to PRW when making attacks with melee hand weapons."),
    ("Lance", "Prowess", "Each level adds to PRW when making attacks with lance weapons."),
    ("Light Artillery", "Poise", "Each level adds to POI when making attacks with light artillery weapons."),
    ("Pistol", "Poise", "Each level adds to POI when making attacks with pistols."),
    ("Rifle", "Poise", "Each level adds to POI when making attacks with rifles."),
    ("Shield", "Prowess", "Each level adds to PRW when attacking with a shield and grants +1 ARM per Shield level against front-arc attacks."),
    ("Thrown Weapon", "Prowess", "Each level adds to PRW when making attacks with thrown weapons or slings."),
    ("Unarmed Combat", "Prowess", "Each level adds to PRW when making attacks bare-handed."),
]

SKILL_DEFS = [
    ("Alchemy", "Intellect", "Occupational", False),
    ("Animal Handling", "Social", "General", True),
    ("Bribery", "Social", "Occupational", False),
    ("Climbing", "Agility", "General", True),
    ("Command", "Social", "Occupational", False),
    ("Craft", "Intellect", "Occupational", False),
    ("Cryptography", "Intellect", "Occupational", False),
    ("Deception", "Social", "Occupational", False),
    ("Detection", "Perception", "General", True),
    ("Disguise", "Intellect", "Occupational", False),
    ("Driving", "Agility", "General", True),
    ("Escape Artist", "Agility", "Occupational", False),
    ("Etiquette", "Social", "Occupational", False),
    ("Fell Calling", "Poise", "Occupational", False),
    ("Forensic Science", "Intellect", "Occupational", False),
    ("Forgery", "Agility or Intellect", "Occupational", False),
    ("Gambling", "Perception", "General", True),
    ("Interrogation", "Intellect", "Occupational", False),
    ("Intimidation", "Social", "General", True),
    ("Jumping", "Physique", "General", True),
    ("Law", "Intellect", "Occupational", False),
    ("Lock Picking", "Agility", "Occupational", False),
    ("Lore", "Intellect", "General", True),
    ("Mechanikal Engineering", "Intellect", "Occupational", False),
    ("Medicine", "Intellect", "Occupational", False),
    ("Navigation", "Perception", "Occupational", False),
    ("Negotiation", "Social", "Occupational", False),
    ("Oratory", "Social", "Occupational", False),
    ("Pickpocket", "Agility", "Occupational", False),
    ("Research", "Intellect", "Occupational", False),
    ("Riding", "Agility", "General", True),
    ("Rope Use", "Agility", "Occupational", False),
    ("Sailing", "Intellect or Strength", "Occupational", False),
    ("Seduction", "Social", "Occupational", False),
    ("Sneak", "Agility", "Occupational", False),
    ("Streetwise", "Perception", "Occupational", False),
    ("Survival", "Perception", "Occupational", False),
    ("Swimming", "Strength", "General", True),
    ("Tracking", "Perception", "Occupational", False),
]

SKILL_NAME_BY_KEY = {simplify(name): (name, stat, category, general) for name, stat, category, general in SKILL_DEFS}
SKILL_NAME_BY_KEY.update({simplify(name): (name, stat, "Military", False) for name, stat, _ in MILITARY_SKILLS})


def actual_skill_heading(line: str) -> tuple[str, str, str, bool] | None:
    match = re.match(r"^(?P<name>.+?)\s*\((?P<stat>[^)]*)\)$", line.strip())
    if not match:
        return None
    raw_name = re.sub(r"\s+", " ", match.group("name")).strip()
    key = simplify(raw_name)
    if key not in SKILL_NAME_BY_KEY:
        return None
    name, stat, category, general = SKILL_NAME_BY_KEY[key]
    normal = f"{name} ({stat})"
    if line.strip() == normal:
        return None
    return name, stat, category, general


def split_skill_text(name: str, text: str) -> dict[str, str]:
    description = text
    untrained = ""
    use = ""
    untrained_match = re.search(rf"\bUntrained\s+{re.escape(name)}\s*:\s*", text, re.I)
    rolls_match = re.search(rf"\b{name.replace(' ', r'\s+')}\s+Rolls\s*:\s*", text, re.I)
    assisted_match = re.search(rf"\bAssisted\s+{re.escape(name)}\s+Rolls\s*:\s*", text, re.I)
    gm_match = re.search(r"\bGame Master Notes\s*:\s*", text, re.I)
    column_boundary = re.search(r"\bMILITARY SKILLS\b|\bMilitary sK\s*ills\b", text, re.I)

    first_marker = min([m.start() for m in [untrained_match, rolls_match, assisted_match, gm_match, column_boundary] if m] or [len(text)])
    description = text[:first_marker].strip()

    if untrained_match:
        end = min([m.start() for m in [rolls_match, assisted_match, gm_match, column_boundary] if m and m.start() > untrained_match.start()] or [len(text)])
        untrained = text[untrained_match.end() : end].strip()
    if rolls_match:
        end = min([m.start() for m in [assisted_match, gm_match] if m and m.start() > rolls_match.start()] or [len(text)])
        use = text[rolls_match.end() : end].strip()

    return {
        "description": normalize_skill_text(description),
        "untrained": normalize_skill_text(untrained),
        "use": normalize_skill_text(use),
    }


SKILL_TEXT_REPLACEMENTS = {
    "NuMBER": "Number",
    "SuRFACE": "Surface",
    "SuBjECT": "Subject",
    "OBjECT": "Object",
    "CIRCuMSTANCES": "Circumstances",
    "SITuATION": "Situation",
    "CONDITIONS": "Conditions",
    "CROWD DYNAMIC": "Crowd Dynamic",
    "ACTION": "Action",
    "ROLL RESuLT": "Roll Result",
    "RESuLT MODIFIER": "Result Modifier",
    "TARGET Number": "Target Number",
    "TARGET NUMBER": "Target Number",
    "DISGuISE": "Disguise",
    "CRYPTOGRAPHY ROLL": "Cryptography Roll",
    "PuRCHASE PRICE": "Purchase Price",
    "MAxIMuM RESALE": "Maximum Resale",
    "CONTRACT OFFER": "Contract Offer",
}


def normalize_skill_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    for bad, good in SKILL_TEXT_REPLACEMENTS.items():
        value = value.replace(bad, good)
    value = value.replace("Disguise’S", "Disguise's").replace("Disguise’s", "Disguise's")
    value = value.replace("A GL", "AGL").replace("A gility", "Agility")
    value = value.replace("2d6 + INT + Disguise level - 2", "2d6 + INT + Disguise level -2")
    value = re.sub(
        r"Disguise'?s Target Number Disguise Creation Circumstances",
        "Disguise target numbers - creation circumstances:",
        value,
        flags=re.I,
    )
    value = re.sub(r"\bTarget Number ([A-Z][A-Za-z ]{2,40})", r"Target Number - \1:", value)
    value = re.sub(r"\bRoll Result ([A-Z][A-Za-z ]{2,40})", r"Roll Result - \1:", value)
    value = re.sub(r"\bResult Modifier ([A-Z][A-Za-z ]{2,40})", r"Result Modifier - \1:", value)
    value = value.replace(" : ", ": ")
    return re.sub(r"\s+", " ", value).strip()


def extract_skills(reader: PdfReader) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    for name, stat, summary in MILITARY_SKILLS:
        skills.append(
            {
                "id": simplify(name),
                "name": name,
                "category": "Military",
                "governingStat": stat,
                "general": False,
                "summary": summary,
                "description": summary,
                "untrained": "Military skills can be used untrained.",
                "use": summary,
                "bookPage": 172,
                "pageStart": 172,
                "pageEnd": 172,
                "pdfPageStart": 173,
                "pdfPageEnd": 173,
                "source": source_for_pages(172),
            }
        )

    records = clean_page_records(reader, 173, 196)
    sections: list[tuple[tuple[str, str, str, bool], int, list[dict[str, Any]]]] = []
    current: tuple[str, str, str, bool] | None = None
    current_start = 0
    current_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        heading = actual_skill_heading(record["text"])
        if heading:
            if current:
                sections.append((current, current_start, current_records))
            current = heading
            current_start = index
            current_records = []
            continue
        if current:
            current_records.append(record)
    if current:
        sections.append((current, current_start, current_records))

    seen = {simplify(name) for name, _, _ in MILITARY_SKILLS}
    for (name, stat, category, general), _, section_records in sections:
        if simplify(name) in seen:
            continue
        text = cleaned_joined_lines([record["text"] for record in section_records])
        split = split_skill_text(name, text)
        start_page = section_records[0]["bookPage"] if section_records else 172
        end_page = section_records[-1]["bookPage"] if section_records else start_page
        if name == "Alchemy":
            end_page = 173
            split["use"] = split["use"] or (
                "Make an INT + Alchemy roll against a target number set by the Game Master or formula. "
                "Alchemy covers substance identification, crafting alchemical items, field alchemy, and ingredient extraction."
            )
        skills.append(
            {
                "id": simplify(name),
                "name": name,
                "category": category,
                "governingStat": stat,
                "general": general,
                "summary": split["description"].split(".")[0].strip() + "." if split["description"] else "",
                **split,
                "bookPage": start_page,
                "pageStart": start_page,
                "pageEnd": end_page,
                "pdfPageStart": section_records[0]["pdfPage"] if section_records else start_page + 1,
                "pdfPageEnd": end_page + 1,
                "source": source_for_pages(start_page, end_page),
            }
        )
        seen.add(simplify(name))

    return sorted(skills, key=lambda item: (item["category"], item["name"]))


COMBAT_PAGE_ENDS = {
    "rolls": 200,
    "initiative-rounds": 202,
    "turn-structure": 203,
    "movement": 204,
    "actions": 206,
    "attacks": 214,
    "damage": 215,
    "injuries": 218,
    "continuous-effects": 218,
    "knockdown": 219,
    "feat-points": 220,
    "terrain": 224,
    "fear": 224,
    "light": 225,
    "arcane-traditions": 230,
    "will-weavers": 229,
    "focusers": 230,
    "rune-shot-spells": 231,
    "control-area": 231,
    "casting-a-spell": 232,
    "magic-attacks": 233,
    "upkeep-spells": 233,
    "channeling": 234,
}


def apply_static_page_ranges(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for entry in entries:
        start = entry.get("pageStart", entry.get("bookPage"))
        if start is None:
            continue
        end = entry.get("pageEnd", COMBAT_PAGE_ENDS.get(entry.get("id"), start))
        entry["bookPage"] = start
        entry["pageStart"] = start
        entry["pageEnd"] = end
        if "pdfPage" in entry:
            entry["pdfPageStart"] = entry["pdfPage"]
            entry["pdfPageEnd"] = entry["pdfPage"] + (end - start)
        entry.setdefault("source", source_for_pages(start, end))
    return entries


def combat_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "rolls",
            "title": "Core Rolls",
            "category": "Basics",
            "bookPage": 197,
            "summary": "Most checks roll 2d6 plus a stat and sometimes a skill. Meeting or exceeding the target number succeeds.",
            "rules": [
                "Skill Roll = 2d6 + Stat + Skill Level.",
                "Attribute Roll = 2d6 + relevant Stat.",
                "Contested rolls compare totals; highest total succeeds, ties are draws.",
                "A boosted roll adds one additional die.",
                "A d3 means roll d6, halve it, and round up.",
            ],
        },
        {
            "id": "initiative-rounds",
            "title": "Initiative and Rounds",
            "category": "Combat Flow",
            "bookPage": 201,
            "summary": "Combat proceeds in rounds. Each character takes a turn in initiative order.",
            "rules": [
                "Initiative = 2d6 + Initiative plus applicable bonuses.",
                "Ties roll off to determine order.",
                "New combatants roll initiative at the start of the next round.",
                "Steamjacks activate during their controller's turn, before or after the controller moves and acts.",
                "Held activation delays only the Activation Phase; Maintenance and Control still resolve in order.",
            ],
        },
        {
            "id": "turn-structure",
            "title": "Turn Structure",
            "category": "Combat Flow",
            "bookPage": 203,
            "summary": "A turn has Maintenance, Control, and Activation phases.",
            "rules": [
                "Maintenance: expire continuous effects, then resolve remaining continuous effects.",
                "Control: pay upkeep costs or spells expire, then resolve other Control Phase effects.",
                "Activation: move and act. Actions can happen before or after movement, but movement cannot be interrupted by actions.",
            ],
        },
        {
            "id": "movement",
            "title": "Movement",
            "category": "Movement",
            "bookPage": 203,
            "summary": "Characters generally move by full advance, run, or charge.",
            "rules": [
                "Full advance: move up to current SPD in inches.",
                "Run: advance up to 2x SPD; the character can make one quick action but cannot attack, make full actions, or cast spells.",
                "Charge: advance SPD + 3 inches toward a visible enemy in a straight line.",
                "A successful charge ends with the target in melee range. If the character moved at least 3 inches and hits with the first melee attack, the damage roll is boosted.",
                "A failed charge immediately ends the character's turn.",
            ],
        },
        {
            "id": "actions",
            "title": "Actions",
            "category": "Actions",
            "bookPage": 205,
            "summary": "Characters choose between quick actions, attacks, and full actions during Activation.",
            "rules": [
                "Choose one: two quick actions; attack plus one quick action; or one full action.",
                "Common quick actions include drawing/stowing items, reloading, pulling a grenade pin, casting a spell, activating a runeplate, using a drive, taking cover, or going prone.",
                "Dropping an item does not require an action; picking it up does.",
            ],
        },
        {
            "id": "attacks",
            "title": "Attacks",
            "category": "Attacking",
            "bookPage": 207,
            "summary": "Melee, ranged, and magic attacks roll 2d6 plus the relevant attack stat and modifiers.",
            "rules": [
                "Melee attacks use PRW + weapon skill + weapon attack modifier.",
                "Ranged attacks use POI + weapon skill + weapon attack modifier.",
                "Magic attacks use ARC + modifiers.",
                "A critical hit occurs when any two dice in the attack roll show the same number and the attack hits.",
                "Spray and AOE attacks have special targeting and template rules.",
            ],
        },
        {
            "id": "damage",
            "title": "Damage",
            "category": "Damage",
            "bookPage": 215,
            "summary": "Damage rolls compare POW against ARM; excess becomes damage points.",
            "rules": [
                "Ranged, magic, and most other damage rolls: 2d6 + POW.",
                "Melee damage rolls: 2d6 + POW + STR.",
                "Boosted damage adds one additional die.",
                "Damage points equal the amount by which the damage roll exceeds ARM.",
                "An attack with POW '-' does not cause damage.",
            ],
        },
        {
            "id": "injuries",
            "title": "Disabled and Injuries",
            "category": "Damage",
            "bookPage": 216,
            "summary": "A character disabled after all vitality is marked becomes incapacitated and rolls on the Injury Table.",
            "rules": [
                "Incapacitated characters cannot act and have no command range.",
                "Grievously injured characters die unless stabilized within rounds equal to PHY.",
                "Stabilizing requires a full action while B2B and an INT + Medicine roll against TN 14.",
                "After a short rest, a character regains vitality equal to PHY, then 1 per hour for three hours, then 1 every six hours.",
            ],
        },
        {
            "id": "continuous-effects",
            "title": "Continuous Effects",
            "category": "Effects",
            "bookPage": 218,
            "summary": "Continuous effects may expire at the start of the affected character's Maintenance Phase.",
            "rules": [
                "Roll d6 for each continuous effect: 1-2 expires; 3-6 remains.",
                "Resolve remaining continuous effects simultaneously after all expiration rolls.",
                "Corrosion deals d3 damage points unless it expires.",
                "Fire causes a POW 12 fire damage roll unless it expires.",
            ],
        },
        {
            "id": "knockdown",
            "title": "Knockdown and Knockout",
            "category": "Effects",
            "bookPage": 219,
            "summary": "Knocked down and knocked out characters are extremely vulnerable and lose major options.",
            "rules": [
                "Melee attacks against knocked down or stationary characters automatically hit.",
                "A knocked down character has base DEF 5, no melee range, does not engage, and does not block line of sight.",
                "Standing up requires forfeiting either movement or actions.",
                "A knocked out character makes a WIL roll vs TN 14 at the start of each turn to regain consciousness.",
            ],
        },
        {
            "id": "feat-points",
            "title": "Feat Points",
            "category": "Heroics",
            "bookPage": 220,
            "summary": "Feat points fuel heroic rerolls, extra actions, recovery, and common feats.",
            "rules": [
                "Player characters start each session with three feat points and can have at most three.",
                "Common gains include defeating enemies, critical success on skill or attack rolls, and GM awards.",
                "Common spends include boost non-attack skill roll, Heroic Dodge, extra quick action, Parry, Relentless Charge, reroll failed roll, Run and Gun, Shake effects, Sprint, Two-Fister, and Walk It Off.",
            ],
        },
        {
            "id": "terrain",
            "title": "Terrain",
            "category": "Terrain",
            "bookPage": 221,
            "summary": "Terrain changes movement, line of sight, and defensive bonuses.",
            "rules": [
                "Terrain categories include open, rough, and difficult.",
                "Obstacles can provide cover and may require movement to climb.",
                "Forests are rough terrain, grant concealment to models inside, and block line of sight through more than 3 inches of forest.",
                "Shallow water counts as rough terrain.",
            ],
        },
        {
            "id": "fear",
            "title": "Fear and Terror",
            "category": "Morale",
            "bookPage": 224,
            "summary": "Terrifying situations force Willpower rolls, with escalating results from anxiety to panic.",
            "rules": [
                "Unaffected characters do not roll again unless the situation worsens or a higher terror target appears.",
                "Anxiety grants +1 STR but imposes -1 on skill rolls and prevents intentional movement toward the source.",
                "Panic imposes -2 on skill rolls and can force the character to flee or freeze.",
            ],
        },
        {
            "id": "light",
            "title": "Light and Darkness",
            "category": "Visibility",
            "bookPage": 225,
            "summary": "Lighting controls concealment, stealth, and Sneak bonuses.",
            "rules": [
                "Bright light has no default bonus or penalty.",
                "Dim light grants concealment and +2 Sneak.",
                "Complete darkness grants concealment, stealth, and +5 Sneak.",
                "Light sources have bright and dim radius bands; the GM may alter distances for smoke, storms, ash, or wind.",
            ],
        },
        {
            "id": "arcane-traditions",
            "title": "Arcane Traditions",
            "category": "Magic",
            "bookPage": 228,
            "summary": "A Gifted character's arcane tradition determines which spellcasting rules he uses.",
            "rules": [
                "All Gifted characters begin with an arcane tradition that does not change.",
                "Characters without the Warcaster career are will weavers.",
                "Characters with the Warcaster career are focusers.",
                "Will weavers generate fatigue to cast and upkeep spells; focusers spend focus points.",
            ],
        },
        {
            "id": "will-weavers",
            "title": "Will Weavers and Fatigue",
            "category": "Magic",
            "bookPage": 229,
            "summary": "Will weavers cast by gaining fatigue points and risk exhaustion when they push past ARC.",
            "rules": [
                "A will weaver gains fatigue equal to a spell's COST when casting it.",
                "Upkeeping a spell adds 1 fatigue during each Control Phase.",
                "Boosting a magic attack or magic damage roll adds 1 fatigue.",
                "A will weaver can gain 1 fatigue to increase a spell's RNG by 5 inches once per casting; CTRL and SP spells cannot be extended this way.",
                "Will weavers remove fatigue equal to ARC each Maintenance Phase.",
                "If fatigue exceeds ARC, make a fatigue roll after each spell; roll 2d6 equal to or above current fatigue or become exhausted.",
                "An exhausted character's turn ends immediately and he cannot cast spells during the next round.",
            ],
        },
        {
            "id": "focusers",
            "title": "Focusers and Focus Points",
            "category": "Magic",
            "bookPage": 230,
            "summary": "Focusers receive focus each Control Phase and spend it for spells, upkeep, boosts, attacks, and steamjacks.",
            "rules": [
                "During each Control Phase, a focuser receives focus points equal to ARC.",
                "Casting a spell costs focus equal to the spell's COST.",
                "Upkeeping each spell costs 1 focus during the Control Phase.",
                "A focuser can spend 1 focus to boost magic attack and magic damage rolls.",
                "A focuser can spend focus for additional attacks with bonded mechanika weapons.",
                "A focuser can allocate up to 3 focus points to each steamjack in his battlegroup and control area.",
                "Remove all focus points from the focuser and his battlegroup at the start of each Maintenance Phase.",
            ],
        },
        {
            "id": "rune-shot-spells",
            "title": "Rune Shot Spells",
            "category": "Magic",
            "bookPage": 230,
            "summary": "Gun mages cast rune shot spells onto magelock ammunition before firing.",
            "rules": [
                "Gun Mage is not an arcane tradition; a gun mage can be a will weaver or a focuser.",
                "Rune shot spells must be cast on the turn they take effect and affect only the next magelock shot.",
                "Rune shot spells do not require quick actions.",
                "Any number of rune shot spells can be cast on a single shot, but the same rune shot spell can empower a round only once.",
                "Each round can have only one rune shot spell with an AOE.",
                "A directly hit target suffers the ranged attack and all empowered spell effects.",
            ],
        },
        {
            "id": "control-area",
            "title": "Control Area",
            "category": "Magic",
            "bookPage": 231,
            "summary": "Gifted characters have a measurable control area used by spells, focus allocation, and channeling.",
            "rules": [
                "A control area is centered on the character and extends from the base edge a number of inches equal to ARC x 2.",
                "A character is always in his own control area.",
                "A character can measure his control area at any time.",
                "Spells with RNG or AOE of CTRL use the spellcaster's control area.",
                "A steamjack must be in its warcaster's control area to receive focus or channel spells.",
            ],
        },
        {
            "id": "casting-a-spell",
            "title": "Casting a Spell",
            "category": "Magic",
            "bookPage": 231,
            "summary": "Spellcasting pays COST, declares a legal target, measures range, and resolves immediately.",
            "rules": [
                "A spell can be cast multiple times per Activation Phase if its COST is paid each time.",
                "Except for rune shot spells, casting a spell is a quick action.",
                "A character cannot cast a spell during a turn in which he runs.",
                "Pay COST first: will weavers gain fatigue, focusers spend focus.",
                "If an upkeep spell is cast again by the same caster, previous instances immediately expire.",
                "Declare a target in line of sight, subject to targeting rules.",
                "Non-offensive spells with numeric RNG can also target the spell's point of origin.",
                "If a non-offensive spell is in range, it immediately takes effect; if out of range, it has no effect.",
            ],
        },
        {
            "id": "magic-attacks",
            "title": "Offensive Spells and Magic Attacks",
            "category": "Magic",
            "bookPage": 232,
            "summary": "Offensive spells require magic attack rolls and follow most ranged attack rules.",
            "rules": [
                "Magic Attack Roll = 2d6 + ARC.",
                "A boosted magic attack roll adds one additional die.",
                "A direct hit occurs when the attack roll equals or exceeds the target's DEF.",
                "All 1s automatically miss; all 6s are a direct hit unless rolling only one die.",
                "Magic attack rolls do not suffer the target-in-melee penalty when the attacker is in melee with the target.",
                "If an offensive spell with an AOE misses or is out of range, its point of impact deviates.",
            ],
        },
        {
            "id": "upkeep-spells",
            "title": "Upkeep Spells",
            "category": "Magic",
            "bookPage": 233,
            "summary": "Upkeep spells remain in play if the caster pays upkeep during the Control Phase.",
            "rules": [
                "Will weavers gain 1 fatigue for each upkeep spell they maintain; warcasters spend 1 focus for each.",
                "A character can maintain an upkeep outside his control area up to ARC x 10 inches.",
                "If an upkeep spell is not maintained, it immediately expires.",
                "A character can have only one offensive and one non-offensive upkeep spell on him at a time.",
                "A caster can recast an upkeep spell already in play; the previous casting expires when the new COST is paid.",
                "Outside combat, a character can upkeep a number of spells equal to ARC.",
                "If the caster is destroyed or removed from play, his upkeep spells and next-turn-expiring spells immediately expire.",
            ],
        },
        {
            "id": "channeling",
            "title": "Channeling",
            "category": "Magic",
            "bookPage": 233,
            "summary": "Channelers act as spell relays, changing a spell's point of origin.",
            "rules": [
                "A channeler must be in the spellcaster's control area.",
                "The spellcaster casts the spell, but the channeler becomes the spell's point of origin.",
                "The channeler must have line of sight to the spell's target; the spellcaster does not need line of sight to the channeler or target.",
                "A channeler engaged by an enemy cannot channel spells.",
                "A stationary channeler can channel; a knocked down channeler cannot.",
                "A RNG SELF spell cannot be channeled.",
                "A channeler can be the target of a non-offensive spell it channels, but cannot be the target of an offensive spell it channels.",
                "A spellcaster can channel through only one channeler at a time.",
            ],
        },
    ]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(r"C:\Users\happy\Project\IKRPG-Tools\Iron_Kingdoms_Full_Metal_Fantasy_Roleplaying_Game_Core_Rules.pdf"),
    )
    parser.add_argument("--out", type=Path, default=Path("src/data"))
    args = parser.parse_args()

    reader = read_pdf(args.pdf)
    races = apply_static_page_ranges(extract_races())
    careers = extract_careers(reader)
    spells = extract_spells(reader)
    price_items = extract_price_list(reader)
    details = extract_item_details(reader, price_items)
    details.update(manual_item_details())
    items = merge_items(price_items, details)
    combat = apply_static_page_ranges(combat_cards())
    benefits = extract_benefits(reader)
    abilities = extract_abilities(reader)
    skills = extract_skills(reader)

    meta = {
        "title": "Iron Kingdoms RPG Tools Data",
        "source": args.pdf.name,
        "generatedBy": "scripts/extract_ikrpg.py",
        "counts": {
            "races": len(races),
            "careers": len(careers),
            "gameCards": len(combat),
            "combatCards": len(combat),
            "benefits": len(benefits),
            "abilities": len(abilities),
            "skills": len(skills),
            "spells": len(spells),
            "items": len(items),
            "itemDetails": sum(1 for item in items if item.get("description") or item.get("specialRules")),
        },
    }

    write_json(args.out / "races.json", races)
    write_json(args.out / "careers.json", careers)
    write_json(args.out / "combat.json", combat)
    write_json(args.out / "benefits.json", benefits)
    write_json(args.out / "abilities.json", abilities)
    write_json(args.out / "skills.json", skills)
    write_json(args.out / "spells.json", spells)
    write_json(args.out / "items.json", items)
    write_json(args.out / "meta.json", meta)
    print(json.dumps(meta["counts"], indent=2))


if __name__ == "__main__":
    main()
