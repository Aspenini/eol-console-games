#!/usr/bin/env python3
"""
Extract game data from Wikipedia HTML files into organized JSON databases.
Supports multiple consoles with dynamic table structure detection and proper date parsing.
"""

import re
import json
import os
import glob
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup


def extract_console_name(filename: str) -> str:
    """Extract console name from HTML filename."""
    # Common console mappings - ORDER MATTERS! More specific first
    console_mappings = [
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
        
        ('nintendo 3ds', 'nintendo3ds'),
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
    
    for key, console in console_mappings:
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, filename_lower):
            return console
    
    for key, console in console_mappings:
        if key in filename_lower:
            return console
    
    return 'unknown'


def clean_text(text: str) -> str:
    """Clean text from HTML elements."""
    if not text:
        return ''
    text = ' '.join(text.split())
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\(c\)|\(d\)|\(e\)|\(f\)', '', text)
    return text.strip()


def parse_date_cell(cell) -> str:
    """
    Parse a date cell from HTML, handling nested spans and multiple dates.
    Returns ISO 8601 date (YYYY-MM-DD or YYYY-MM for month-only) or empty string if cannot parse.
    Also checks for data-sort-value attribute which often contains the actual date.
    """
    if not cell:
        return ''
    
    # First, check for data-sort-value attribute (often contains the actual ISO date)
    sort_value = cell.get('data-sort-value', '').strip()
    if sort_value:
        # Parse sort value (often format: YYYYMMDD or YYYY-MM-DD)
        # Remove any prefix like "00000000" or "000000001"
        sort_value = re.sub(r'^0+', '', sort_value)
        
        # Try to parse as YYYYMMDD
        if len(sort_value) >= 8 and sort_value.isdigit():
            try:
                date_str = sort_value[:8]
                dt = datetime.strptime(date_str, '%Y%m%d')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Try YYYY-MM-DD format
        if re.match(r'\d{4}-\d{2}-\d{2}', sort_value):
            try:
                dt = datetime.strptime(sort_value[:10], '%Y-%m-%d')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    # Remove all display:none spans (hidden sorting values)
    for span in cell.find_all('span', style=re.compile(r'display\s*:\s*none')):
        span.decompose()
    
    # Also check for span with data-sort-value
    span_sort = cell.find('span', {'data-sort-value': True})
    if span_sort:
        span_value = span_sort.get('data-sort-value', '').strip()
        if span_value:
            # Parse sort value (format: YYYYMMDD prefix like "000000001996-03-01-0000" or "19960301")
            span_value = re.sub(r'^0+', '', span_value)
            if len(span_value) >= 8 and span_value[:8].isdigit():
                try:
                    date_str = span_value[:8]
                    dt = datetime.strptime(date_str, '%Y%m%d')
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass
    
    # Get all visible text
    text = clean_text(cell.get_text())
    
    if not text or text.lower() in ['unreleased', 'tba', 'tbd', '—', '—', 'n/a', 'na']:
        return ''
    
    # If there are multiple dates separated by <br>, take the first one
    text = text.split('\n')[0].strip()
    
    # Parse common date formats
    date_patterns = [
        (r'(\w+)\s+(\d{1,2}),\s+(\d{4})', '%B %d, %Y'),  # August 1, 1999
        (r'(\w+)\s+(\d{1,2})\s+(\d{4})', '%B %d %Y'),    # August 1 1999
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),    # 08/01/1999
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),        # 1999-08-01
        (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),            # 19990801
        (r'(\w+)\s+(\d{4})', '%B %Y'),                   # March 1996
    ]
    
    # Try each pattern
    for pattern, format_str in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if format_str == '%Y%m%d':
                    # Direct format from matched groups
                    date_str = match.group(0)
                    dt = datetime.strptime(date_str, format_str)
                    return dt.strftime('%Y-%m-%d')
                elif format_str == '%B %Y':
                    # Month and year only - use first day of month
                    date_str = match.group(0)
                    dt = datetime.strptime(date_str, format_str)
                    return dt.strftime('%Y-%m-%d')
                else:
                    # Reconstruct from matched groups
                    date_str = match.group(0)
                    dt = datetime.strptime(date_str, format_str)
                    return dt.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                continue
    
    # If we couldn't parse, return empty
    return ''


def get_link_or_italic_text(cell) -> str:
    """Get text from link if available, otherwise get italic or all text."""
    link = cell.find('a')
    if link:
        return clean_text(link.get_text())
    
    italic = cell.find('i')
    if italic:
        text = clean_text(italic.string or '')
        if not text:
            text = clean_text(italic.get_text())
        return text
    
    return clean_text(cell.get_text())


def analyze_table_structure(table) -> Dict:
    """
    Analyze table headers to determine column structure.
    Returns dictionary mapping field names to column indices.
    """
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
        'brazil_col': None,
        'br_col': None,
        'uses_row_headers': False,
        'has_region_header_row': False
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
    
    # Check if first data row is actually region headers
    if rows and len(rows) > 1:
        first_row_cells = rows[1].find_all(['td', 'th'])
        if first_row_cells:
            first_cell_text = first_row_cells[0].get_text(strip=True).lower()
            # Check if it's a region name
            region_keywords = ['japan', 'jp', 'north america', 'na', 'europe', 'eu', 'pal', 'australasia', 'australia', 'brazil', 'br']
            if any(keyword in first_cell_text for keyword in region_keywords):
                structure['has_region_header_row'] = True
    
    # Find header row(s) - start from index 0, stop before region header row if it exists
    header_rows = []
    stop_idx = len(rows)
    if structure['has_region_header_row']:
        stop_idx = 1  # Only look at row 0 for headers
    
    for i in range(min(stop_idx, 3)):
        cells = rows[i].find_all(['th', 'td'])
        if cells:
            header_text = ' '.join([cell.get_text(strip=True).lower() for cell in cells])
            if any(keyword in header_text for keyword in ['title', 'developer', 'publisher', 'release']):
                header_rows.append((i, rows[i]))
    
    if not header_rows:
        header_rows = [(0, rows[0])]
    
    # Get all header cells accounting for colspan
    all_headers = []
    for _, row in header_rows:
        cells = row.find_all(['th', 'td'])
        for cell in cells:
            text = cell.get_text(strip=True).lower()
            # Special handling: if region header row exists, don't expand colspan for "release date"
            # We'll map regions from the region header row instead
            if structure['has_region_header_row'] and 'release' in text and 'date' in text:
                colspan = 1  # Don't expand
            else:
                colspan = int(cell.get('colspan', 1))
            for _ in range(colspan):
                all_headers.append(text)
    
    # Map headers to column indices
    for idx, header_text in enumerate(all_headers):
        header_lower = header_text.strip().lower()
        
        if structure['title_col'] is None:
            if any(keyword in header_lower for keyword in ['title', 'game', 'name']):
                structure['title_col'] = idx
        
        if structure['developer_col'] is None:
            if 'developer' in header_lower:
                structure['developer_col'] = idx
        
        if structure['publisher_col'] is None:
            if 'publisher' in header_lower:
                structure['publisher_col'] = idx
        
        if structure['first_released_col'] is None:
            if any(keyword in header_lower for keyword in ['first released', 'release date', 'released', 'first release']) and 'japan' not in header_lower:
                structure['first_released_col'] = idx
        
        # Skip regional mapping if region header row exists (we'll handle it specially below)
        if not structure['has_region_header_row']:
            if 'japan' in header_lower or header_lower.strip() in ['jp', 'j']:
                if structure['jp_col'] is None:
                    structure['jp_col'] = idx
            if 'north america' in header_lower or header_lower.strip() in ['na', 'north']:
                if structure['na_col'] is None:
                    structure['na_col'] = idx
            if 'pal' in header_lower and 'europe' not in header_lower:
                if structure['pal_col'] is None:
                    structure['pal_col'] = idx
            if 'europe' in header_lower and '/pal' not in header_lower:
                if structure['europe_col'] is None:
                    structure['europe_col'] = idx
            if 'australasia' in header_lower or ('australia' in header_lower and 'australasia' not in header_lower):
                if structure['australasia_col'] is None:
                    structure['australasia_col'] = idx
            if 'brazil' in header_lower or (header_lower.strip() == 'br'):
                if structure['brazil_col'] is None:
                    structure['brazil_col'] = idx
                if structure['br_col'] is None:
                    structure['br_col'] = idx
    
    # Special handling for tables with region header rows - use row 1 for regional mapping
    if structure['has_region_header_row'] and rows and len(rows) > 1:
        # Calculate the offset: where the region columns start in the actual data rows
        # In data rows, rowspan=2 cells appear as normal cells, so count them
        header_row_cells = rows[0].find_all(['th', 'td'])
        region_row_cells = rows[1].find_all(['th', 'td'])
        
        # Count columns that will appear in data rows
        # Cells with rowspan=2 appear in data rows, cells with colspan expand
        columns_in_data_rows = 0
        for cell in header_row_cells:
            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            if rowspan >= 2:
                # This cell spans to data rows - counts as 1 column in data rows
                columns_in_data_rows += 1
            elif 'release' in cell.get_text(strip=True).lower() and 'date' in cell.get_text(strip=True).lower():
                # This is the "Release date" colspan - regions start right after this
                # Don't count the colspan, regions replace it
                break
            else:
                # Regular column that doesn't span rows
                columns_in_data_rows += colspan
        
        # Now map regions from row 1 (these cells show the region names)
        # Find where the region cells start in row 1
        region_start_idx = None
        for idx, cell in enumerate(region_row_cells):
            cell_text = cell.get_text(strip=True).lower().strip()
            if cell_text and (cell_text in ['jp', 'j', 'na', 'pal', 'europe', 'eu', 'brazil', 'br'] or 
                             any(word in cell_text for word in ['japan', 'north america', 'australasia', 'australia'])):
                if region_start_idx is None:
                    region_start_idx = idx
                # Map this region
                actual_idx = columns_in_data_rows + (idx - region_start_idx)
                if 'japan' in cell_text or cell_text == 'jp' or cell_text == 'j':
                    structure['jp_col'] = actual_idx
                if 'north america' in cell_text or cell_text == 'na':
                    structure['na_col'] = actual_idx
                if 'pal' in cell_text:
                    structure['pal_col'] = actual_idx
                if 'europe' in cell_text or cell_text == 'eu':
                    structure['europe_col'] = actual_idx
                if 'australasia' in cell_text or 'australia' in cell_text:
                    structure['australasia_col'] = actual_idx
                if 'brazil' in cell_text or cell_text == 'br':
                    structure['brazil_col'] = actual_idx
                    structure['br_col'] = actual_idx
    
    if structure['uses_row_headers']:
        structure['title_col'] = 0
    
    return structure


def extract_cell_data(cells: List, structure: Dict, console_name: str) -> Dict:
    """Extract data from table cells using detected structure."""
    game = {}
    
    # Handle row headers (th scope="row" for title)
    if structure.get('uses_row_headers'):
        if cells and len(cells) > 0:
            first_cell = cells[0]
            if first_cell.name == 'th' and first_cell.get('scope') == 'row':
                game['title'] = get_link_or_italic_text(first_cell)
                adjusted_cells = cells[1:]
                adjusted_structure = {k: (v - 1 if v is not None and v > 0 else v) 
                                     for k, v in structure.items() if k.endswith('_col')}
            else:
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
    
    # Extract first released (use it for release_date calculation but don't store separately)
    first_col = adjusted_structure.get('first_released_col')
    if first_col is not None and len(adjusted_cells) > first_col:
        date_str = parse_date_cell(adjusted_cells[first_col])
        if date_str:
            # Store temporarily as first_released for release_date calculation, will be removed in normalization
            game['first_released'] = date_str
    
    # Extract regional releases
    jp_col = adjusted_structure.get('jp_col')
    if jp_col is not None and len(adjusted_cells) > jp_col:
        date_str = parse_date_cell(adjusted_cells[jp_col])
        if date_str:
            game['jp_release'] = date_str
    
    na_col = adjusted_structure.get('na_col')
    if na_col is not None and len(adjusted_cells) > na_col:
        date_str = parse_date_cell(adjusted_cells[na_col])
        if date_str:
            game['na_release'] = date_str
    
    pal_col = adjusted_structure.get('pal_col')
    if pal_col is not None and len(adjusted_cells) > pal_col:
        date_str = parse_date_cell(adjusted_cells[pal_col])
        if date_str:
            game['pal_release'] = date_str
    
    europe_col = adjusted_structure.get('europe_col')
    if europe_col is not None and len(adjusted_cells) > europe_col:
        date_str = parse_date_cell(adjusted_cells[europe_col])
        if date_str:
            game['europe_release'] = date_str
    
    australasia_col = adjusted_structure.get('australasia_col')
    if australasia_col is not None and len(adjusted_cells) > australasia_col:
        date_str = parse_date_cell(adjusted_cells[australasia_col])
        if date_str:
            game['australasia_release'] = date_str
    
    brazil_col = adjusted_structure.get('brazil_col') or adjusted_structure.get('br_col')
    if brazil_col is not None and len(adjusted_cells) > brazil_col:
        date_str = parse_date_cell(adjusted_cells[brazil_col])
        if date_str:
            game['brazil_release'] = date_str
            game['br_release'] = date_str
    
    return game


def normalize_game_data(game: Dict) -> Dict:
    """
    Normalize game data: preserve ALL original fields from Wikipedia.
    Additionally adds a 'release_date' field with the earliest available release date.
    All other fields are kept as-is from the extraction.
    """
    # Start with a copy of all original fields
    normalized = {}
    for key, value in game.items():
        if isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value
    
    # Ensure basic fields exist (even if empty)
    if 'title' not in normalized:
        normalized['title'] = ''
    if 'developer' not in normalized:
        normalized['developer'] = ''
    if 'publisher' not in normalized:
        normalized['publisher'] = ''
    
    # Collect all release dates and find the earliest one for release_date field
    release_dates = []
    date_fields = [
        'first_released', 'jp_release', 'na_release', 'pal_release', 
        'europe_release', 'australasia_release', 'brazil_release', 'br_release', 'release_date'
    ]
    
    for field in date_fields:
        date_value = normalized.get(field, '').strip()
        if date_value:
            release_dates.append(date_value)
    
    # Sort dates and use the earliest one for release_date
    if release_dates:
        try:
            # Parse and sort dates to find earliest
            parsed_dates = []
            for date_str in release_dates:
                try:
                    # Handle both YYYY-MM-DD and YYYY-MM formats
                    if len(date_str) >= 10:
                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    elif len(date_str) >= 7:
                        dt = datetime.strptime(date_str[:7], '%Y-%m')
                    else:
                        continue
                    parsed_dates.append((dt, date_str))
                except ValueError:
                    continue
            
            if parsed_dates:
                # Sort by date (earliest first)
                parsed_dates.sort(key=lambda x: x[0])
                normalized['release_date'] = parsed_dates[0][1]
            else:
                # If no valid dates found, use first non-empty
                normalized['release_date'] = release_dates[0]
        except Exception:
            # If parsing fails, just use the first non-empty date
            normalized['release_date'] = release_dates[0]
    else:
        # No release dates found
        normalized['release_date'] = ''
    
    # Remove first_released field since release_date already contains this information
    normalized.pop('first_released', None)
    
    return normalized


def create_game_key(game: Dict) -> str:
    """
    Create a unique key for a game based on title, developer, and publisher.
    Used for deduplication. Normalizes text for comparison.
    """
    title = game.get('title', '').strip().lower()
    developer = game.get('developer', '').strip().lower()
    publisher = game.get('publisher', '').strip().lower()
    
    # Normalize by removing extra whitespace and special characters
    title = ' '.join(title.split())
    developer = ' '.join(developer.split())
    publisher = ' '.join(publisher.split())
    
    return f"{title}|||{developer}|||{publisher}"


def deduplicate_games(games: List[Dict]) -> List[Dict]:
    """
    Remove duplicate games from a list. If duplicates found, keep the one with the most complete data.
    """
    seen = {}
    result = []
    
    for game in games:
        key = create_game_key(game)
        
        if key not in seen:
            seen[key] = game
            result.append(game)
        else:
            # Merge data if duplicate - prefer non-empty values
            existing = seen[key]
            
            # Check if current game has more complete data
            existing_completeness = sum(1 for k in ['title', 'developer', 'publisher', 'release_date'] 
                                       if existing.get(k, '').strip())
            current_completeness = sum(1 for k in ['title', 'developer', 'publisher', 'release_date'] 
                                      if game.get(k, '').strip())
            
            # Replace if current is more complete, or if it has a release_date and existing doesn't
            if (current_completeness > existing_completeness) or \
               (not existing.get('release_date', '').strip() and game.get('release_date', '').strip()):
                # Update the existing entry in seen and find it in result to replace
                seen[key] = game
                for i, r_game in enumerate(result):
                    if create_game_key(r_game) == key:
                        result[i] = game
                        break
    
    return result


def detect_categories(soup) -> List[str]:
    """Detect which categories exist in the HTML by analyzing section headers."""
    categories = []
    sections = soup.find_all(['h2', 'h3'])
    
    section_texts = [s.get_text(strip=True).lower() for s in sections]
    
    # Map section names to category names
    category_mapping = {
        'licensed games': 'licensed',
        'unlicensed games': 'unlicensed',
        'championship games': 'championship',
        'konami qta': 'konami_qta',
        'konami qta adaptor games': 'konami_qta',
        'unreleased games': 'unreleased',
    }
    
    for section_text in section_texts:
        for key, category in category_mapping.items():
            if key in section_text and category not in categories:
                categories.append(category)
    
    # If no categories detected, default to licensed
    if not categories:
        categories = ['licensed']
    
    return categories


def find_game_tables(soup, category: str = None) -> List:
    """Find game tables in the HTML, optionally filtered by category."""
    found_tables = []
    
    # Strategy 1: Find tables with id="softwarelist"
    licensed_tables = soup.find_all('table', {'id': 'softwarelist'})
    if licensed_tables:
        for table in licensed_tables:
            rows = table.find_all('tr')
            if len(rows) > 5:
                found_tables.append(table)
    
    # Strategy 2: Find large wikitable tables
    if not found_tables:
        all_tables = soup.find_all('table', class_=lambda x: x and 'wikitable' in x)
        for table in all_tables:
            rows = table.find_all('tr')
            if len(rows) > 10:
                header_row = rows[0] if rows else None
                if header_row:
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                    header_text = ' '.join(headers)
                    has_title = any(kw in header_text for kw in ['title', 'game', 'name'])
                    has_dev_or_pub = any(kw in header_text for kw in ['developer', 'publisher'])
                    
                    if has_title and has_dev_or_pub:
                        data_row_count = 0
                        for row in rows[1:6]:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                first_cell = cells[0]
                                if first_cell.find('a') or first_cell.find('i'):
                                    data_row_count += 1
                        
                        if data_row_count >= 2:
                            found_tables.append(table)
                            break
    
    return found_tables


def parse_game_table(table, console_name: str) -> List[Dict]:
    """Parse game table by analyzing actual structure."""
    games = []
    rows = table.find_all('tr')
    
    if len(rows) < 2:
        return games
    
    # Analyze structure
    structure = analyze_table_structure(table)
    
    # Find start index (skip header rows and region header rows)
    start_idx = 1
    if structure['has_region_header_row']:
        start_idx = 2
    
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
        date_str = parse_date_cell(cells[3])
        if date_str:
            game['jp_release'] = date_str
        
        if game.get('title'):
            games.append(game)
    
    return games


def extract_with_bs4(html_content: str, console_name: str) -> Dict[str, List[Dict]]:
    """Extract game data from HTML content."""
    soup = BeautifulSoup(html_content, 'lxml')
    tables = defaultdict(list)
    
    # Detect which categories exist
    categories = detect_categories(soup)
    
    # Find all game tables
    game_tables = find_game_tables(soup)
    
    for table in game_tables:
        games = parse_game_table(table, console_name)
        if games:
            # Add to 'licensed' for now (main games table)
            tables['licensed'].extend(games)
    
    # Check for special tables
    unreleased_table = soup.find('table', {'id': 'softwarelistunreleased'})
    if unreleased_table:
        tables['unreleased'] = parse_unreleased_table(unreleased_table)
    
    konami_table = soup.find('table', {'id': 'konamiqtalist'})
    if konami_table:
        tables['konami_qta'] = parse_konami_qta_table(konami_table)
    
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
                tables_data = extract_with_bs4(html_content, console_name)
            except Exception as e:
                print(f"    [WARNING] Error with BeautifulSoup: {e}")
                continue
            
            # Merge games from this file into console's tables
            for table_name, games in tables_data.items():
                if games:
                    # Normalize games before adding (consolidate release dates)
                    normalized_games = [normalize_game_data(game) for game in games]
                    console_tables[table_name].extend(normalized_games)
                    print(f"    [OK] Extracted {len(normalized_games)} games from {table_name}")
                else:
                    print(f"    [NO DATA] No games found for {table_name}")
        
        # Combine all games from all tables (licensed, unreleased, etc.)
        all_games = []
        for table_name, games in console_tables.items():
            # Deduplicate games per table first
            if games:
                before_count = len(games)
                games = deduplicate_games(games)
                after_count = len(games)
                if before_count != after_count:
                    print(f"    [INFO] Deduplicated {table_name}: {before_count} -> {after_count} games")
                
                # Only include games with at least a title
                games = [g for g in games if g.get('title', '').strip()]
                
                # Add all games to the combined list
                all_games.extend(games)
        
        # Final deduplication across all categories
        if all_games:
            before_count = len(all_games)
            all_games = deduplicate_games(all_games)
            after_count = len(all_games)
            if before_count != after_count:
                print(f"[INFO] Final deduplication: {before_count} -> {after_count} total games")
            
            # Save single JSON file in database root (no folders)
            final_games = []
            for game in all_games:
                # Keep ALL fields from Wikipedia, just ensure title exists
                if game.get('title', '').strip():
                    final_games.append(game)
            
            if final_games:
                output_file = os.path.join(database_folder, f'{console_name}.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(final_games, f, indent=2, ensure_ascii=False)
                print(f"[OK] Saved {len(final_games)} games to database/{console_name}.json")
        
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
