#!/usr/bin/env python3
"""
Check for exact duplicate games across all JSON files.
Finds games that have identical data in multiple files.
"""

import json
import os
from collections import defaultdict
from typing import List, Dict, Tuple


def load_json_file(filename: str) -> List[Dict]:
    """Load a JSON file and return its contents."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] File not found: {filename}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse {filename}: {e}")
        return []


def normalize_game_data(game: Dict) -> str:
    """Convert game data to a normalized string for comparison."""
    # Remove category field as it's used for organization
    normalized = game.copy()
    normalized.pop('category', None)
    
    # Sort keys and convert to JSON string for exact matching
    return json.dumps(normalized, sort_keys=True)


def find_duplicates_in_file(data: List[Dict], filename: str) -> List[Tuple[int, Dict]]:
    """Find duplicates within a single file."""
    duplicates = []
    seen = {}
    
    for i, game in enumerate(data):
        normalized = normalize_game_data(game)
        if normalized in seen:
            duplicates.append((i, game))
        else:
            seen[normalized] = i
    
    return duplicates


def find_duplicates_across_files() -> Dict:
    """Find all duplicate games across all JSON files."""
    
    # Find all JSON files in the database directory
    json_files = []
    database_dir = 'database'
    
    if os.path.exists(database_dir):
        for root, dirs, files in os.walk(database_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
    
    all_data = {}
    for filename in json_files:
        if os.path.exists(filename):
            all_data[filename] = load_json_file(filename)
    
    # Track which games appear in which files
    game_locations = defaultdict(list)
    
    for filename, games in all_data.items():
        for i, game in enumerate(games):
            normalized = normalize_game_data(game)
            game_locations[normalized].append((filename, i))
    
    # Find duplicates (games appearing in multiple files or multiple times in same file)
    results = {
        'internal_duplicates': {},  # Duplicates within same file
        'cross_file_duplicates': [],  # Games appearing in multiple files
        'stats': {
            'total_unique_games': len(game_locations),
            'total_game_entries': sum(len(games) for games in all_data.values())
        }
    }
    
    # Check for internal duplicates in each file
    for filename, games in all_data.items():
        duplicates = find_duplicates_in_file(games, filename)
        if duplicates:
            results['internal_duplicates'][filename] = duplicates
    
    # Check for cross-file duplicates
    for normalized_game, locations in game_locations.items():
        if len(locations) > 1:
            # Get the actual game data from first location
            filename, index = locations[0]
            game = all_data[filename][index]
            
            results['cross_file_duplicates'].append({
                'game': game,
                'locations': locations,
                'count': len(locations)
            })
    
    # Sort cross-file duplicates by count (highest first)
    results['cross_file_duplicates'].sort(key=lambda x: x['count'], reverse=True)
    
    return results


def print_results(results: Dict):
    """Pretty print the duplicate analysis results."""
    
    print("=" * 80)
    print("GAME DATABASE DUPLICATE ANALYSIS")
    print("=" * 80)
    
    # Print statistics
    stats = results['stats']
    print(f"\n[STATISTICS]")
    print(f"   Total unique games: {stats['total_unique_games']}")
    print(f"   Total game entries: {stats['total_game_entries']}")
    if stats['total_game_entries'] > 0:
        print(f"   Duplicate rate: {((stats['total_game_entries'] - stats['total_unique_games']) / stats['total_game_entries'] * 100):.1f}%")
    else:
        print("   Duplicate rate: 0.0% (no games found)")
    
    # Print internal duplicates
    internal = results['internal_duplicates']
    if internal:
        print(f"\n[WARNING] Internal Duplicates (within same file):")
        for filename, duplicates in internal.items():
            print(f"\n   {filename}:")
            print(f"   Found {len(duplicates)} duplicate entries")
            for idx, game in duplicates[:5]:  # Show first 5
                print(f"      Row {idx + 1}: {game.get('title', 'Unknown')}")
            if len(duplicates) > 5:
                print(f"      ... and {len(duplicates) - 5} more")
    else:
        print("\n[OK] No internal duplicates found")
    
    # Print cross-file duplicates
    cross_file = results['cross_file_duplicates']
    print(f"\n[CROSS-FILE DUPLICATES]")
    print(f"   Games appearing in multiple locations: {len(cross_file)}")
    
    if cross_file:
        print(f"\n   Top 20 most duplicated games:")
        for i, dup_info in enumerate(cross_file[:20], 1):
            game = dup_info['game']
            locations = dup_info['locations']
            count = dup_info['count']
            
            title = game.get('title', 'Unknown')
            print(f"\n   {i}. '{title}' (appears {count} times)")
            print(f"      Locations:")
            for filename, index in locations:
                print(f"         - {filename}, row {index + 1}")
    else:
        print("   [OK] No cross-file duplicates found")
    
    print("\n" + "=" * 80)


def main():
    """Main function."""
    # Set UTF-8 encoding for Windows console
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("Loading JSON files...")
    results = find_duplicates_across_files()
    
    print_results(results)
    
    # Save detailed results to JSON
    output_file = 'duplicate_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] Detailed results saved to: {output_file}")


if __name__ == '__main__':
    main()

