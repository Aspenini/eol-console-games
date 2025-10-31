# Game Database Extractor

A Python tool to extract game data from Wikipedia HTML pages and convert them into structured JSON databases.

## Overview

This project extracts comprehensive game information from Wikipedia game list pages, organizing the data into clean, structured JSON files. Perfect for building game databases, web applications, or data analysis projects.

## Features

✅ **Multi-Console Support** - Process HTML files from any Wikipedia game list  
✅ **Automatic Table Detection** - Finds and extracts data from multiple tables per console  
✅ **Clean Data** - Removes citations, normalizes text, handles Unicode properly  
✅ **Organized Output** - Separate category files + combined master files  
✅ **Duplicate Detection** - Built-in verification to ensure data quality  

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Extractor

Place your Wikipedia HTML files in the `html/` folder, then run:

```bash
python extract_games.py
```

This will process all HTML files and create organized JSON databases for each console.

---

## Output Files

The extractor creates JSON files in a structured `database/` folder:

### Console-Specific Folders

Each console gets its own folder: `database/{console_name}/`

### Individual Table Files

### 1. `database/{console_name}/licensed.json`
**Purpose:** All officially licensed games

**Contents:** Varies by console (NES: 1,376 games)  
**Fields:** 
- `title` - Game title
- `developer` - Development company
- `publisher` - Publishing company
- `first_released` - Earliest release date
- `jp_release` - Japan release date (if released)
- `na_release` - North America release date (if released)
- `pal_release` - Europe/Australia release date (if released)

### 2. `database/{console_name}/unreleased.json`
**Purpose:** Games that were announced/cancelled but never released

**Contents:** Varies by console (NES: 86 games)  
**Fields:**
- `title` - Game title
- `year` - Planned release year
- `publisher` - Publishing company
- `regions` - Planned release regions

### 3. `database/{console_name}/konami_qta.json` (NES only)
**Purpose:** Educational games released for the Konami QTa Adaptor

**Contents:** 7 games (NES only)  
**Fields:** Title, Developer, Publisher, JP Release

### 4. `database/{console_name}_all.json` (Combined Master File)
**Purpose:** **Combined master file** containing all games from all categories

**Contents:** All games combined (NES: 1,469 total)  
**Extra Field:** Each game has a `category` field indicating its source

---

## Data Examples

### Licensed Game:
```json
{
  "title": "Super Mario Bros.",
  "developer": "Nintendo EAD",
  "publisher": "Nintendo",
  "first_released": "September 13, 1985",
  "jp_release": "September 13, 1985",
  "na_release": "October 18, 1985",
  "pal_release": "May 15, 1987"
}
```

### Unreleased Game:
```json
{
  "title": "Bio Force Ape",
  "year": "1992",
  "publisher": "SETA",
  "regions": "JP"
}
```

### Combined Game (with category):
```json
{
  "title": "Super Mario Bros.",
  "developer": "Nintendo EAD",
  "publisher": "Nintendo",
  "first_released": "September 13, 1985",
  "jp_release": "September 13, 1985",
  "na_release": "October 18, 1985",
  "pal_release": "May 15, 1987",
  "category": "licensed"
}
```

---

## How It Works

The extractor reads HTML files from Wikipedia game list pages and:

1. **Finds tables** using common Wikipedia table IDs
2. **Extracts data** from each row and column
3. **Cleans text** by removing citations, handling Unicode, normalizing whitespace
4. **Organizes output** into separate JSON files by category
5. **Creates combined** master file with all games

### Table Detection (Wikipedia HTML)

- **Primary:** Tables with `id="softwarelist"` (standard Wikipedia format)
- **Fallback:** First large wikitable with game list columns (for custom formats)
- **Additional:** Unreleased games, Konami QTa tables (when available)

---

## Data Quality

### Current Database Statistics

**Total Consoles:** 24 different systems processed

**Game Counts (Sample):**
- Nintendo DS: 3,466 games
- PlayStation 2: 4,344 games
- PlayStation: 4,073 games
- Nintendo 3DS: 1,806 games
- SNES: 1,749 games
- NES: 1,471 games
- Wii: 1,626 games
- PlayStation Vita: 1,480 games
- PlayStation 3: 2,408 games
- And many more...

### Verification

Run the duplicate checker to verify data quality:

```bash
python check_duplicates.py
```

✅ **Results:** No unexpected duplicates found  
✅ Individual files contain unique entries  
✅ Combined files properly merge all categories  

---

## Usage Examples

### Supported Consoles

The extractor automatically detects and processes games from:

- **Nintendo:** NES, SNES, N64, Game Boy, Game Boy Color, Game Boy Advance, Nintendo DS, Nintendo 3DS, GameCube, Wii, Wii U
- **PlayStation:** PS1, PS2, PS3, PSP, PS Vita
- **Sega:** Genesis, Saturn, Dreamcast, Sega CD, 32X, Game Gear, Master System
- **And many more!**

Place HTML files from Wikipedia game lists in the `html/` folder with their original filenames. The extractor will automatically detect the console and extract all game data.

---

## Building a Static Website

Generate a beautiful static website from your game database:

```bash
python build_site.py
```

This creates a `site/` directory with:
- **index.html** - Main page with all consoles
- **console.html** - Browse games by console (with search & pagination)
- **style.css** - Clean, modern styling (no gradients)
- **script.js** - Interactive features (search, filtering)

The site features:
- ✅ **Progressive Enhancement** - Works without JavaScript
- ✅ **Fast Loading** - All data embedded efficiently
- ✅ **Clean Design** - Modern, professional look
- ✅ **Responsive** - Works on mobile and desktop
- ✅ **Search & Filter** - Find games quickly

Simply open `site/index.html` in your browser!

---

## Project Structure

```
GameDatabase/
├── extract_games.py               # Main extraction script
├── build_site.py                   # Static website generator
├── check_duplicates.py             # Duplicate verification tool
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── html/                           # HTML source files folder
│   ├── List of Nintendo...html
│   ├── List of PlayStation...html
│   └── ... (all console HTML files)
├── database/                       # Output JSON files
│   ├── nes/
│   │   ├── licensed.json
│   │   └── ...
│   ├── snes/
│   ├── ps1/
│   └── ..._all.json               # Combined files
└── site/                           # Generated static website
    ├── index.html
    ├── console.html
    ├── style.css
    └── script.js
```

---

## Technical Details

### Dependencies
- **BeautifulSoup4** - HTML parsing
- **lxml** - Fast XML/HTML parser

### Data Cleaning
- Removes citation markers: `[1]`, `[2]`, etc.
- Handles Unicode characters (Japanese, etc.)
- Normalizes whitespace and formatting
- Preserves original date formats

### Limitations
- Column layouts must match expected structure
- Table IDs must be known for each Wikipedia page
- Requires manually downloading HTML files

---

## Data Source

Extracted from Wikipedia pages:
- **NES:** "List of Nintendo Entertainment System games"
- Last updated in source: October 19, 2025
- Comprehensive coverage of all official releases

---

## Contributing

To add support for additional consoles:
1. Download the Wikipedia HTML file
2. Inspect table structures and IDs
3. Update extraction logic as needed
4. Test with duplicate checker

---

## License

Data extracted from Wikipedia is available under the Creative Commons Attribution-ShareAlike 4.0 License.

---

## Summary

✅ **Clean, structured JSON data**  
✅ **Multi-console support framework**  
✅ **Automatic duplicate detection**  
✅ **Ready for database/web app integration**  
✅ **Comprehensive game information**  

Perfect for building retro game databases, analysis projects, or preservation efforts!
