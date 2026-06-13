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
    lines = clean_lines(pages_text(reader, 237, 246))
    spells: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    description: list[str] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        text = " ".join(description)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\bCOST RNG AOE POW UP OFF\b", "", text, flags=re.I).strip()
        current["description"] = text
        current["tags"] = spell_tags(current, text)
        spells.append(current)
        current = None
        description = []

    index = 0
    while index < len(lines):
        line = lines[index]
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
            current = {
                "id": simplify(raw_name),
                "name": canonical_name or canonical_spell_name(raw_name),
                "rawName": raw_name,
                "cost": matched.group("cost"),
                "range": normalize_stat(matched.group("rng")),
                "aoe": normalize_stat(matched.group("aoe")),
                "pow": normalize_stat(matched.group("pow")),
                "upkeep": matched.group("up").lower() == "yes",
                "offensive": matched.group("off").lower() == "yes",
                "offensiveMode": normalize_stat(matched.group("off")),
                "bookPage": 236 + (index // 999999),
                "source": "Iron Kingdoms Full Metal Fantasy Roleplaying Game Core Rules, Spell Descriptions pp. 236-245",
            }
            index += consumed
            continue
        if current:
            description.append(line)
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
PRICE_RE = re.compile(r"^(?P<name>.+?)\s+(?P<price>\+?\d+\+?\s*gc\+?|\d+\+\s*gc|\d+\s*gc(?:\s*each)?|\d+)$", re.I)


def extract_price_list(reader: PdfReader) -> list[dict[str, Any]]:
    lines = clean_lines(pages_text(reader, 248, 252))
    items: list[dict[str, Any]] = []
    category: str | None = None
    buffer = ""

    for line in lines:
        if line.upper() == "ARMOR":
            break
        key = simplify(line)
        if key in PRICE_CATEGORY_KEYS:
            category = PRICE_CATEGORY_KEYS[key]
            buffer = ""
            continue
        if category is None or line.lower().startswith("price lists"):
            continue
        candidate = f"{buffer} {line}".strip() if buffer else line
        match = PRICE_RE.match(candidate)
        if match:
            name = normalize_item_name(match.group("name"))
            items.append(
                {
                    "id": f"{simplify(category)}-{simplify(name)}",
                    "name": name,
                    "category": category,
                    "price": normalize_price(match.group("price")),
                    "bookPage": None,
                    "source": "Core Rules price lists pp. 247-251",
                }
            )
            buffer = ""
        else:
            sentence_like = len(line) > 90 or bool(re.search(r"[.!?]\s*$", line))
            buffer = "" if sentence_like else candidate
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
    r"^(Cost|Skill|Attack Modifier|POW|Ammo|Effective Range|Extreme Range|AOE|SPD Modifier|DEF Modifier|ARM Modifier):\s*(.+)$",
    re.I,
)


def extract_item_details(reader: PdfReader, price_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    names = {simplify(item["name"]): item["name"] for item in price_items}
    lines = clean_lines(pages_text(reader, 252, 278))
    details: dict[str, dict[str, Any]] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        key = simplify(line)
        if key in names and any(next_line.lower().startswith("cost:") for next_line in lines[index + 1 : index + 5]):
            item_name = names[key]
            block: list[str] = [line]
            index += 1
            while index < len(lines):
                next_key = simplify(lines[index])
                if next_key in names and any(next_line.lower().startswith("cost:") for next_line in lines[index + 1 : index + 5]):
                    break
                if lines[index].isupper() and ":" not in lines[index] and len(lines[index]) > 4:
                    break
                block.append(lines[index])
                index += 1
            details[simplify(item_name)] = parse_item_block(item_name, block)
            continue
        index += 1
    return details


def parse_item_block(name: str, block: list[str]) -> dict[str, Any]:
    fields: dict[str, str] = {}
    description: list[str] = []
    special: list[str] = []
    section = ""

    for line in block[1:]:
        hit = FIELD_RE.match(line)
        if hit:
            fields[hit.group(1).lower().replace(" ", "_")] = hit.group(2).strip()
            section = ""
            continue
        if line.lower().startswith("description"):
            section = "description"
            rest = re.sub(r"^description\s*:?\s*", "", line, flags=re.I).strip()
            if rest:
                description.append(rest)
            continue
        if line.lower().startswith("special rules"):
            section = "special"
            rest = re.sub(r"^special rules\s*:?\s*", "", line, flags=re.I).strip()
            if rest:
                special.append(rest)
            continue
        if section == "description":
            description.append(line)
        elif section == "special":
            special.append(line)

    return {
        "name": name,
        "fields": fields,
        "description": re.sub(r"\s+", " ", " ".join(description)).strip(),
        "specialRules": re.sub(r"\s+", " ", " ".join(special)).strip(),
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
    lines = clean_lines(pages_text(reader, 116, 118))
    benefits: list[dict[str, Any]] = []
    current_archetype: str | None = None
    current: dict[str, Any] | None = None
    description: list[str] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        current["description"] = re.sub(r"\s+", " ", " ".join(description)).strip()
        current["tags"] = classify_rules_text(current["name"] + " " + current["description"])
        benefits.append(current)
        current = None
        description = []

    for line in lines:
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
                "bookPage": 115,
                "source": "Core Rules archetype benefits pp. 115-117",
            }
            if rest:
                description.append(rest)
        elif current:
            description.append(line)
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
    lines = clean_lines(pages_text(reader, 158, 169))
    abilities: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    description: list[str] = []

    def finalize() -> None:
        nonlocal current, description
        if not current:
            return
        current["description"] = re.sub(r"\s+", " ", " ".join(description)).strip()
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
                "source": "Core Rules abilities pp. 157-168",
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
            description.append(line)
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
    races = extract_races()
    spells = extract_spells(reader)
    price_items = extract_price_list(reader)
    details = extract_item_details(reader, price_items)
    items = merge_items(price_items, details)
    combat = combat_cards()
    benefits = extract_benefits(reader)
    abilities = extract_abilities(reader)

    meta = {
        "title": "Iron Kingdoms RPG Tools Data",
        "source": args.pdf.name,
        "generatedBy": "scripts/extract_ikrpg.py",
        "counts": {
            "races": len(races),
            "combatCards": len(combat),
            "benefits": len(benefits),
            "abilities": len(abilities),
            "spells": len(spells),
            "items": len(items),
            "itemDetails": sum(1 for item in items if item.get("description") or item.get("specialRules")),
        },
    }

    write_json(args.out / "races.json", races)
    write_json(args.out / "combat.json", combat)
    write_json(args.out / "benefits.json", benefits)
    write_json(args.out / "abilities.json", abilities)
    write_json(args.out / "spells.json", spells)
    write_json(args.out / "items.json", items)
    write_json(args.out / "meta.json", meta)
    print(json.dumps(meta["counts"], indent=2))


if __name__ == "__main__":
    main()
