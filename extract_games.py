#!/usr/bin/env python3
"""
Extract game data from Wikipedia HTML files into organized JSON databases.
Supports multiple consoles with automatic layout detection.
"""

import re
import json
import os
import glob
from collections import defaultdict
from typing import List, Dict


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


def extract_cell_data(cells, num_columns: int) -> Dict:
    """Extract data from table cells, handling different layouts."""
    game = {}
    
    # Different column layouts
    if num_columns == 7:  # NES: Title | Developer | Publisher | First Released | JP | NA | PAL
        if len(cells) >= 7:
            game['title'] = get_link_or_italic_text(cells[0])
            game['developer'] = get_link_or_italic_text(cells[1])
            game['publisher'] = get_link_or_italic_text(cells[2])
            game['first_released'] = get_span_with_sort_value(cells[3])
            
            jp_text = get_span_with_sort_value(cells[4])
            if jp_text and 'unreleased' not in jp_text.lower():
                game['jp_release'] = jp_text
            
            na_text = get_span_with_sort_value(cells[5])
            if na_text and 'unreleased' not in na_text.lower():
                game['na_release'] = na_text
            
            pal_text = get_span_with_sort_value(cells[6])
            if pal_text and 'unreleased' not in pal_text.lower():
                game['pal_release'] = pal_text
    
    elif num_columns == 6:  # Game Boy: Title | Developer | Publisher | JP | NA | PAL
        if len(cells) >= 6:
            game['title'] = get_link_or_italic_text(cells[0])
            game['developer'] = get_link_or_italic_text(cells[1])
            game['publisher'] = get_link_or_italic_text(cells[2])
            
            jp_text = get_span_with_sort_value(cells[3])
            if jp_text and 'unreleased' not in jp_text.lower():
                game['jp_release'] = jp_text
            
            na_text = get_span_with_sort_value(cells[4])
            if na_text and 'unreleased' not in na_text.lower():
                game['na_release'] = na_text
            
            pal_text = get_span_with_sort_value(cells[5])
            if pal_text and 'unreleased' not in pal_text.lower():
                game['pal_release'] = pal_text
    
    elif num_columns == 8:  # SNES: Title | Developer | Publisher | JP | NA | PAL | Ref | (empty)
        if len(cells) >= 6:  # Just need first 6 columns
            game['title'] = get_link_or_italic_text(cells[0])
            game['developer'] = get_link_or_italic_text(cells[1])
            game['publisher'] = get_link_or_italic_text(cells[2])
            
            jp_text = get_span_with_sort_value(cells[3])
            if jp_text and 'unreleased' not in jp_text.lower():
                game['jp_release'] = jp_text
            
            na_text = get_span_with_sort_value(cells[4])
            if na_text and 'unreleased' not in na_text.lower():
                game['na_release'] = na_text
            
            pal_text = get_span_with_sort_value(cells[5])
            if pal_text and 'unreleased' not in pal_text.lower():
                game['pal_release'] = pal_text
    
    elif num_columns == 9:  # Wii: Title | Developer | Publisher | First Released | JP | NA | Australasia | Europe
        if len(cells) >= 9:
            game['title'] = get_link_or_italic_text(cells[0])
            game['developer'] = get_link_or_italic_text(cells[1])
            game['publisher'] = get_link_or_italic_text(cells[2])
            game['first_released'] = get_span_with_sort_value(cells[3])
            
            jp_text = get_span_with_sort_value(cells[4])
            if jp_text and 'unreleased' not in jp_text.lower():
                game['jp_release'] = jp_text
            
            na_text = get_span_with_sort_value(cells[5])
            if na_text and 'unreleased' not in na_text.lower():
                game['na_release'] = na_text
            
            # Australasia
            aus_text = get_span_with_sort_value(cells[6])
            if aus_text and 'unreleased' not in aus_text.lower():
                game['australasia_release'] = aus_text
            
            # Europe
            pal_text = get_span_with_sort_value(cells[7])
            if pal_text and 'unreleased' not in pal_text.lower():
                game['europe_release'] = pal_text
    
    elif num_columns == 11:  # Game Boy Advance: Title | Developer | Publisher | Release | JP | NA | EU/PAL | AU | KR | Multiplayer
        if len(cells) >= 4:
            # Handle <th scope="row"> for title
            title_cell = cells[0]
            if title_cell.name == 'th' and title_cell.get('scope') == 'row':
                game['title'] = get_link_or_italic_text(title_cell)
            else:
                game['title'] = get_link_or_italic_text(cells[0])
            
            # Developer (cell[1]) and Publisher (cell[2]) stay normal
            game['developer'] = get_link_or_italic_text(cells[1]) if len(cells) > 1 else ''
            game['publisher'] = get_link_or_italic_text(cells[2]) if len(cells) > 2 else ''
            
            # Release date (cell[3])
            if len(cells) > 3:
                release_date = clean_text(cells[3].get_text())
                if release_date:
                    game['release_dates'] = release_date
            
            # Regions (cells 4-8) are Yes/No indicators
            # We can extract if needed, but they're just checkmarks
    
    return game


def extract_with_bs4(html_content: str) -> Dict[str, List[Dict]]:
    """Extract game data using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = {
            'licensed': [],
            'unlicensed': [],
            'konami_qta': [],
            'unreleased': []
        }
        
        # Licensed games table - find ALL tables with id="softwarelist" and merge them
        licensed_tables = soup.find_all('table', {'id': 'softwarelist'})
        if licensed_tables:
            for table in licensed_tables:
                games = parse_game_table(table)
                tables['licensed'].extend(games)
        
        # Fallback: if no tables with id="softwarelist" found, try to find the first large wikitable
        # This handles Sega Saturn, Dreamcast, and other consoles with different table structures
        if not licensed_tables:
            all_tables = soup.find_all('table', class_='wikitable')
            for table in all_tables:
                # Check if this table looks like a game list (has multiple rows, certain columns)
                rows = table.find_all('tr')
                if len(rows) > 10:  # Reasonable number of games
                    # Try to find headers that suggest it's a game list
                    header_row = rows[0] if rows else None
                    if header_row:
                        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                        # Check if header contains typical game list columns
                        if any(keyword in ' '.join(headers) for keyword in ['title', 'developer', 'publisher', 'release']):
                            games = parse_game_table(table)
                            if games:  # Only use if we actually extracted games
                                tables['licensed'].extend(games)
                                break  # Use the first good table found
        
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


def parse_game_table(table) -> List[Dict]:
    """Parse main licensed games table."""
    from bs4 import BeautifulSoup
    
    games = []
    rows = table.find_all('tr')
    
    if len(rows) < 2:
        return games
    
    # Skip header rows
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        
        if not cells:
            continue
        
        # Determine number of columns
        num_columns = len(cells)
        
        game = extract_cell_data(cells, num_columns)
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
            
            # Extract game tables
            try:
                tables_data = extract_with_bs4(html_content)
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

