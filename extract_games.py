#!/usr/bin/env python3
"""
Extract game data from Wikipedia HTML files into organized JSON databases.
Supports multiple consoles with console-specific table structure detection.
"""

import re
import json
import os
import glob
from collections import defaultdict
from typing import List, Dict, Optional, Tuple


def extract_console_name(filename: str) -> str:
    """Extract console name from HTML filename."""
    # Common console mappings - ORDER MATTERS! More specific first
    # Check longer names first to avoid false matches (e.g., "super nintendo" before "nintendo")
    console_mappings = [
        # Most specific first
        ('super nintendo entertainment system', 'snes'),
        ('super nintendo', 'snes'),
        ('super famicom', 'snes'),
        ('snes', 'snes'),
        
        ('playstation vita', 'playstationvita'),
        ('vita', 'playstationvita'),
        ('psv', 'playstationvita'),
        
        ('playstation portable', 'psp'),
        ('psp', 'psp'),
        
        ('playstation 3', 'playstation3'),
        ('ps3', 'playstation3'),
        
        ('playstation 2', 'playstation2'),
        ('ps2', 'playstation2'),
        
        ('playstation', 'playstation'),  # Must come after playstation 2
        ('ps1', 'playstation'),
        
        ('game boy advance', 'gameboyadvance'),
        ('gba', 'gameboyadvance'),
        
        ('game boy color', 'gameboycolor'),
        ('gbc', 'gameboycolor'),
        
        ('game boy', 'gameboy'),  # Must come after game boy advance/color
        ('gb', 'gameboy'),
        
        ('wii u', 'wiiu'),
        ('wii', 'wii'),
        
        ('nintendo 3ds', 'nintendo3ds'),  # Must come before nintendo ds
        ('3ds', 'nintendo3ds'),
        
        ('nintendo ds', 'nintendods'),
        ('ds', 'nintendods'),
        ('nds', 'nintendods'),
        
        ('nintendo entertainment system', 'nes'),
        ('famicom', 'nes'),
        ('nes', 'nes'),
        
        ('nintendo 64', 'n64'),
        ('n64', 'n64'),
        ('gamecube', 'gamecube'),
        ('gc', 'gamecube'),
        
        # Sega systems
        ('sega genesis', 'genesis'),
        ('sega megadrive', 'genesis'),
        ('genesis', 'genesis'),
        ('mega drive', 'genesis'),
        
        ('sega saturn', 'saturn'),
        ('saturn', 'saturn'),
        
        ('sega cd', 'segacd'),
        ('mega cd', 'segacd'),
        ('segacd', 'segacd'),
        
        ('sega 32x', 'sega32x'),
        ('32x', 'sega32x'),
        
        ('sega dreamcast', 'dreamcast'),
        ('dreamcast', 'dreamcast'),
        
        ('sega game gear', 'gamegear'),
        ('game gear', 'gamegear'),
        
        ('sega master system', 'mastersystem'),
        ('master system', 'mastersystem'),
        
        ('sega pico', 'pico'),
        ('pico', 'pico'),
        
        ('sg-1000', 'sg1000'),
        ('sg1000', 'sg1000'),
        ('sega sg-1000', 'sg1000'),
        ('sega sg1000', 'sg1000'),
    ]
    
    filename_lower = filename.lower()
    
    # Try exact filename matching first (most reliable)
    for key, console in console_mappings:
        # Check if the key appears as a word in the filename
        # This prevents "nintendo entertainment system" matching inside "sega genesis games" HTML
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, filename_lower):
            return console
    
    # Fallback: try substring matching (less reliable, but catches partial matches)
    for key, console in console_mappings:
        if key in filename_lower:
            return console
    
    # Fallback: try to extract a generic name
    return 'unknown'


def clean_text(text: str) -> str:
    """Clean text from HTML elements."""
    if not text:
        return ''
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    # Remove citation patterns like [46], [47], etc.
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\(c\)|\(d\)|\(e\)|\(f\)', '', text)
    return text.strip()


def get_link_or_italic_text(cell) -> str:
    """Get text from link if available, otherwise get italic or all text."""
    from bs4 import BeautifulSoup
    
    link = cell.find('a')
    if link:
        text = clean_text(link.get_text())
        return text
    
    # Try italic text
    italic = cell.find('i')
    if italic:
        text = clean_text(italic.string or '')
        if not text:
            text = clean_text(italic.get_text())
        return text
    
    # Get all text and remove citations
    text = clean_text(cell.get_text())
    return text


def get_span_with_sort_value(cell) -> str:
    """Get text from span with data-sort-value attribute."""
    span = cell.find('span', {'data-sort-value': True})
    if span:
        return clean_text(span.get_text())
    return clean_text(cell.get_text())


def analyze_table_structure(table) -> Dict:
    """
    Analyze table headers in THIS SPECIFIC HTML FILE to determine column structure.
    Returns a dictionary mapping field names to column indices.
    NO HARDCODED ASSUMPTIONS - analyzes the actual table in the file.
    """
    from bs4 import BeautifulSoup
    
    structure = {
        'title_col': None,
        'developer_col': None,
        'publisher_col': None,
        'first_released_col': None,
        'jp_col': None,
        'na_col': None,
        'pal_col': None,
        'europe_col': None,
        'australasia_col': None,
        'other_col': None,
        'uses_row_headers': False  # True if title is in <th scope="row">
    }
    
    rows = table.find_all('tr')
    if len(rows) < 2:
        return structure
    
    # Check if table uses row headers (th scope="row") for titles
    first_data_row = None
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if cells and len(cells) > 0:
            first_cell = cells[0]
            if first_cell.name == 'th' and first_cell.get('scope') == 'row':
                structure['uses_row_headers'] = True
                first_data_row = row
                break
    
    # Find header row(s) - some tables have multi-row headers
    header_rows = []
    for i, row in enumerate(rows[:3]):  # Check first 3 rows
        cells = row.find_all(['th', 'td'])
        if cells:
            header_text = ' '.join([cell.get_text(strip=True).lower() for cell in cells])
            if any(keyword in header_text for keyword in ['title', 'developer', 'publisher', 'release', 'japan', 'north', 'europe', 'pal']):
                header_rows.append((i, row))
    
    if not header_rows:
        # Fallback: assume first row is header
        header_rows = [(0, rows[0])]
    
    # Get all header cells across header rows, accounting for colspan
    all_headers = []
    header_row_cells_list = []  # Store actual cell objects for reference
    
    for _, row in header_rows:
        cells = row.find_all(['th', 'td'])
        row_headers = []
        for cell in cells:
            text = cell.get_text(strip=True).lower()
            colspan = int(cell.get('colspan', 1))
            rowspan = int(cell.get('rowspan', 1))
            for _ in range(colspan):
                all_headers.append(text)
                row_headers.append((text, cell))
        header_row_cells_list.extend([cell for _, cell in row_headers])
    
    # Map headers to column indices based on ACTUAL headers found in this table
    for idx, header_text in enumerate(all_headers):
        header_lower = header_text.strip().lower()
        
        # Title detection - check various title variations
        if structure['title_col'] is None:
            if any(keyword in header_lower for keyword in ['title', 'game', 'name']):
                structure['title_col'] = idx
        
        # Developer detection
        if structure['developer_col'] is None:
            if 'developer' in header_lower:
                structure['developer_col'] = idx
        
        # Publisher detection
        if structure['publisher_col'] is None:
            if 'publisher' in header_lower:
                structure['publisher_col'] = idx
        
        # First released detection
        if structure['first_released_col'] is None:
            if any(keyword in header_lower for keyword in ['first released', 'release date', 'released', 'first release']):
                structure['first_released_col'] = idx
        
        # Regional releases - be more specific to avoid conflicts
        if 'japan' in header_lower or header_lower.strip() in ['jp', 'j']:
            if structure['jp_col'] is None:
                structure['jp_col'] = idx
        if 'north america' in header_lower or header_lower.strip() in ['na', 'north']:
            if structure['na_col'] is None:
                structure['na_col'] = idx
        if 'pal' in header_lower and 'europe' not in header_lower:  # Avoid matching both PAL and Europe
            if structure['pal_col'] is None:
                structure['pal_col'] = idx
        if 'europe' in header_lower and '/pal' not in header_lower:  # Don't match "Europe/PAL" as just Europe
            if structure['europe_col'] is None:
                structure['europe_col'] = idx
        if 'australasia' in header_lower or ('australia' in header_lower and 'australasia' not in header_lower):
            if structure['australasia_col'] is None:
                structure['australasia_col'] = idx
        if header_lower.strip() == 'other':
            if structure['other_col'] is None:
                structure['other_col'] = idx
    
    # If using row headers, title_col should be 0 (it's the th scope="row")
    if structure['uses_row_headers']:
        structure['title_col'] = 0
    
    return structure


# REMOVED: get_console_specific_structure
# We now rely entirely on actual header detection from each HTML file
# No more hardcoded console-specific assumptions!


def extract_cell_data(cells: List, structure: Dict, console_name: str) -> Dict:
    """
    Extract data from table cells using console-specific structure.
    """
    game = {}
    
    # Handle row headers (th scope="row" for title)
    if structure.get('uses_row_headers'):
        if cells and len(cells) > 0:
            first_cell = cells[0]
            if first_cell.name == 'th' and first_cell.get('scope') == 'row':
                game['title'] = get_link_or_italic_text(first_cell)
                # Adjust indices - skip the title th
                adjusted_cells = cells[1:]
                adjusted_structure = {k: (v - 1 if v is not None and v > 0 else v) 
                                     for k, v in structure.items() if k.endswith('_col')}
            else:
                # Not using row headers but structure says we should
                adjusted_cells = cells
                adjusted_structure = structure
                if structure.get('title_col') is not None:
                    game['title'] = get_link_or_italic_text(cells[structure['title_col']])
        else:
            return game
    else:
        adjusted_cells = cells
        adjusted_structure = structure
        if structure.get('title_col') is not None and len(cells) > structure['title_col']:
            game['title'] = get_link_or_italic_text(cells[structure['title_col']])
    
    # Extract developer
    dev_col = adjusted_structure.get('developer_col')
    if dev_col is not None and len(adjusted_cells) > dev_col:
        game['developer'] = get_link_or_italic_text(adjusted_cells[dev_col])
    
    # Extract publisher
    pub_col = adjusted_structure.get('publisher_col')
    if pub_col is not None and len(adjusted_cells) > pub_col:
        game['publisher'] = get_link_or_italic_text(adjusted_cells[pub_col])
    
    # Extract first released
    first_col = adjusted_structure.get('first_released_col')
    if first_col is not None and len(adjusted_cells) > first_col:
        text = get_span_with_sort_value(adjusted_cells[first_col])
        if text and 'unreleased' not in text.lower():
            game['first_released'] = text
    
    # Extract regional releases
    jp_col = adjusted_structure.get('jp_col')
    if jp_col is not None and len(adjusted_cells) > jp_col:
        text = get_span_with_sort_value(adjusted_cells[jp_col])
        if text and 'unreleased' not in text.lower():
            game['jp_release'] = text
    
    na_col = adjusted_structure.get('na_col')
    if na_col is not None and len(adjusted_cells) > na_col:
        text = get_span_with_sort_value(adjusted_cells[na_col])
        if text and 'unreleased' not in text.lower():
            game['na_release'] = text
    
    pal_col = adjusted_structure.get('pal_col')
    if pal_col is not None and len(adjusted_cells) > pal_col:
        text = get_span_with_sort_value(adjusted_cells[pal_col])
        if text and 'unreleased' not in text.lower():
            game['pal_release'] = text
    
    europe_col = adjusted_structure.get('europe_col')
    if europe_col is not None and len(adjusted_cells) > europe_col:
        text = get_span_with_sort_value(adjusted_cells[europe_col])
        if text and 'unreleased' not in text.lower():
            game['europe_release'] = text
    
    australasia_col = adjusted_structure.get('australasia_col')
    if australasia_col is not None and len(adjusted_cells) > australasia_col:
        text = get_span_with_sort_value(adjusted_cells[australasia_col])
        if text and 'unreleased' not in text.lower():
            game['australasia_release'] = text
    
    other_col = adjusted_structure.get('other_col')
    if other_col is not None and len(adjusted_cells) > other_col:
        text = get_span_with_sort_value(adjusted_cells[other_col])
        if text and 'unreleased' not in text.lower():
            game['other_release'] = text
    
    return game


def find_game_tables(soup) -> List:
    """
    Find all game tables in THIS HTML FILE by analyzing structure.
    Returns list of table elements that contain game data.
    """
    from bs4 import BeautifulSoup
    
    found_tables = []
    
    # Strategy 1: Find tables with id="softwarelist" (standard Wikipedia format)
    licensed_tables = soup.find_all('table', {'id': 'softwarelist'})
    if licensed_tables:
        for table in licensed_tables:
            # Verify it actually looks like a game table
            rows = table.find_all('tr')
            if len(rows) > 5:  # Has some data
                found_tables.append(table)
    
    # Strategy 2: Find large wikitable tables that contain game data
    if not found_tables:
        all_tables = soup.find_all('table', class_=lambda x: x and 'wikitable' in x)
        for table in all_tables:
            rows = table.find_all('tr')
            if len(rows) > 10:  # Reasonable number of rows
                # Check if header row contains game-related keywords
                header_row = rows[0] if rows else None
                if header_row:
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                    header_text = ' '.join(headers)
                    # Must have title AND (developer OR publisher) to be a game table
                    has_title = any(kw in header_text for kw in ['title', 'game', 'name'])
                    has_dev_or_pub = any(kw in header_text for kw in ['developer', 'publisher'])
                    
                    if has_title and has_dev_or_pub:
                        # Check a few data rows to confirm it's actually game data
                        data_row_count = 0
                        for row in rows[1:6]:  # Check first 5 potential data rows
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:  # Has multiple columns
                                # Check if first cell looks like a game title (has link or italic)
                                first_cell = cells[0]
                                if first_cell.find('a') or first_cell.find('i'):
                                    data_row_count += 1
                        
                        if data_row_count >= 2:  # At least 2 rows look like games
                            found_tables.append(table)
                            break  # Use the first good table found
    
    return found_tables


def extract_with_bs4(html_content: str, console_name: str) -> Dict[str, List[Dict]]:
    """
    Extract game data by analyzing THIS HTML FILE's actual table structure.
    No hardcoded assumptions - each file is analyzed individually.
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = {
            'licensed': [],
            'unlicensed': [],
            'konami_qta': [],
            'unreleased': []
        }
        
        # Find all game tables in THIS HTML FILE
        game_tables = find_game_tables(soup)
        
        for table in game_tables:
            games = parse_game_table(table, console_name)
            if games:
                tables['licensed'].extend(games)
        
        # Unreleased games table
        unreleased_table = soup.find('table', {'id': 'softwarelistunreleased'})
        if unreleased_table:
            tables['unreleased'] = parse_unreleased_table(unreleased_table)
        
        # Konami QTa games (NES only)
        konami_table = soup.find('table', {'id': 'konamiqtalist'})
        if konami_table:
            tables['konami_qta'] = parse_konami_qta_table(konami_table)
        
        return tables
        
    except ImportError:
        print("BeautifulSoup not installed, falling back to regex parser")
        return extract_all_tables_regex(html_content)


def parse_game_table(table, console_name: str) -> List[Dict]:
    """
    Parse main licensed games table by analyzing THIS SPECIFIC TABLE's structure.
    No hardcoded assumptions - detects structure from actual headers.
    """
    from bs4 import BeautifulSoup
    
    games = []
    rows = table.find_all('tr')
    
    if len(rows) < 2:
        return games
    
    # Analyze THIS TABLE's actual structure from its headers
    structure = analyze_table_structure(table)
    
    # Skip header rows - find first data row
    start_idx = 1
    for i, row in enumerate(rows[1:], 1):
        cells = row.find_all(['td', 'th'])
        if cells:
            # Check if this looks like a data row (has title or multiple cells)
            if len(cells) >= 2:
                start_idx = i
                break
    
    # Parse data rows
    for row in rows[start_idx:]:
        cells = row.find_all(['td', 'th'])
        
        if not cells:
            continue
        
        game = extract_cell_data(cells, structure, console_name)
        if game and game.get('title'):
            games.append(game)
    
    return games


def parse_unreleased_table(table) -> List[Dict]:
    """Parse unreleased games table."""
    from bs4 import BeautifulSoup
    
    games = []
    rows = table.find_all('tr')
    
    if len(rows) < 2:
        return games
    
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        
        if not cells or len(cells) < 4:
            continue
        
        game = {}
        game['title'] = get_link_or_italic_text(cells[0])
        game['year'] = clean_text(cells[1].get_text())
        game['publisher'] = get_link_or_italic_text(cells[2])
        game['regions'] = clean_text(cells[3].get_text())
        
        if game.get('title'):
            games.append(game)
    
    return games


def parse_konami_qta_table(table) -> List[Dict]:
    """Parse Konami QTa games table."""
    from bs4 import BeautifulSoup
    
    games = []
    rows = table.find_all('tr')
    
    if len(rows) < 2:
        return games
    
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        
        if not cells or len(cells) < 4:
            continue
        
        game = {}
        game['title'] = get_link_or_italic_text(cells[0])
        game['developer'] = get_link_or_italic_text(cells[1])
        game['publisher'] = clean_text(cells[2].get_text())
        game['jp_release'] = get_span_with_sort_value(cells[3])
        
        if game.get('title'):
            games.append(game)
    
    return games


def extract_all_tables_regex(html_content: str) -> Dict[str, List[Dict]]:
    """Fallback regex parser (not recommended)."""
    tables = {
        'licensed': [],
        'unlicensed': [],
        'konami_qta': [],
        'unreleased': []
    }
    
    # This is a fallback - BeautifulSoup is much better
    print("[WARNING] Using regex parser - results may be incomplete")
    
    return tables


def main():
    """Main function to extract games from all HTML files."""
    
    # Set up directory structure
    html_folder = 'html'
    database_folder = 'database'
    
    # Create folders if they don't exist
    os.makedirs(html_folder, exist_ok=True)
    os.makedirs(database_folder, exist_ok=True)
    
    # Find all HTML files in html folder
    html_files = glob.glob(os.path.join(html_folder, '*.html'))
    
    if not html_files:
        print(f"[ERROR] No HTML files found in {html_folder}/ folder!")
        print(f"Please place your Wikipedia HTML files in the {html_folder}/ folder.")
        return
    
    print(f"Found {len(html_files)} HTML files to process\n")
    
    # Group HTML files by console name
    console_files = defaultdict(list)
    for html_file in sorted(html_files):
        console_name = extract_console_name(html_file)
        console_files[console_name].append(html_file)
    
    print(f"Processing {len(console_files)} different consoles\n")
    
    # Process each console (which may have multiple HTML files)
    for console_name, html_file_list in sorted(console_files.items()):
        print("=" * 80)
        print(f"Console: {console_name.upper()}")
        print(f"Files: {len(html_file_list)} HTML file(s)")
        print("=" * 80)
        
        # Merge data from all HTML files for this console
        console_tables = defaultdict(list)
        
        for html_file in html_file_list:
            print(f"  Processing: {os.path.basename(html_file)}")
            
            # Read HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract game tables with console-specific parsing
            try:
                tables_data = extract_with_bs4(html_content, console_name)
            except Exception as e:
                print(f"    [WARNING] Error with BeautifulSoup: {e}")
                tables_data = extract_all_tables_regex(html_content)
            
            # Merge games from this file into console's tables
            for table_name, games in tables_data.items():
                if games:
                    console_tables[table_name].extend(games)
                    print(f"    [OK] Extracted {len(games)} games from {table_name}")
                else:
                    print(f"    [NO DATA] No games found for {table_name}")
        
        # Create console-specific folder
        console_folder = os.path.join(database_folder, console_name)
        os.makedirs(console_folder, exist_ok=True)
        
        # Save each table as a separate JSON file in the console folder
        for table_name, games in console_tables.items():
            if games:
                output_file = os.path.join(console_folder, f'{table_name}.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(games, f, indent=2, ensure_ascii=False)
                print(f"[OK] Saved {len(games)} total games to database/{console_name}/{table_name}.json")
        
        # Create combined file in database root
        all_games = []
        for table_name, games in console_tables.items():
            for game in games:
                game_copy = game.copy()
                game_copy['category'] = table_name
                all_games.append(game_copy)
        
        if all_games:
            output_file = os.path.join(database_folder, f'{console_name}_all.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_games, f, indent=2, ensure_ascii=False)
            print(f"[OK] Saved {len(all_games)} total games to database/{console_name}_all.json")
        
        print()  # Empty line between consoles
    
    print("=" * 80)
    print("All extractions complete!")
    print("=" * 80)


if __name__ == '__main__':
    # Set UTF-8 encoding for Windows console
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    main()
