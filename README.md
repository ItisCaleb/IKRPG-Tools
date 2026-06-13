# IKRPG Tools

Iron Kingdoms Full Metal Fantasy RPG quick-reference site.

## Data

The JSON data in `src/data` is generated from the copied Core Rules PDF:

- `races.json`: playable race summaries, stat caps, traits, languages, sizes
- `combat.json`: quick-reference combat cards
- `spells.json`: spell descriptions and spell stats
- `items.json`: price lists plus parsed item details when available

Re-run extraction:

```powershell
python .\scripts\extract_ikrpg.py --pdf .\Iron_Kingdoms_Full_Metal_Fantasy_Roleplaying_Game_Core_Rules.pdf --out .\src\data
```

The encrypted PDF requires `pypdf` plus `cryptography`.

## Development

```powershell
npm install
npm run dev
npm run build
npm run preview
```

## Docker

Build and run with Docker Compose:

```powershell
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8080
```

Build only:

```powershell
docker build -t ikrpg-tools:latest .
```

The Docker image serves the built static site with Nginx. PDFs are excluded from
the image build context by `.dockerignore`.

## Layout

The interface is responsive:

- desktop: fixed navigation rail, list pane, and detail pane
- tablet: off-canvas navigation with backdrop
- mobile: stacked list/detail panes, compact filters, and dynamic viewport height
