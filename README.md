# EOL Console Games Database

A static archive of games from discontinued consoles that have reached end of life. Data extracted from Wikipedia.

## Overview

* **25 Consoles** — Complete catalog of EOL systems
* **33,712+ Games** — Titles sourced from official Wikipedia lists
* **Smart Search** — Shortcuts like “gta” → *Grand Theft Auto*
* **Accent-Insensitive** — “pokemon” matches *Pokémon*
* **Clean, Verified Data** — Citations removed, duplicates checked
* **Dark Mode & Responsive Design** — Auto theme detection
* **Multi-Console Support** — Handles different table formats per console

## Data Output

Each console’s data is stored under `database/{console_name}/`:

* **licensed.json** — Released games
* **unreleased.json** — Cancelled/never-released titles
* **{console}_all.json** — Combined data with category field
* **konami_qta.json** — (NES only) Educational titles

### Example Entry

```json
{
  "title": "Super Mario Bros.",
  "developer": "Nintendo EAD",
  "publisher": "Nintendo",
  "first_released": "September 13, 1985"
}
```

## Supported Consoles

**Nintendo:** NES, SNES, N64, GameCube, Wii, Wii U, GB, GBC, GBA, DS, 3DS
**PlayStation:** PS1, PS2, PS3, PSP, PS Vita
**Sega:** Genesis, Saturn, Dreamcast, Sega CD, 32X, Game Gear, Master System, SG-1000, Pico