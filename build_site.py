#!/usr/bin/env python3
"""
Build a static website from the game database JSON files.
Creates a clean, modern site with embedded data and progressive enhancement.
"""

import json
import os
from collections import defaultdict
from typing import Dict, List
import html


def load_all_games() -> Dict[str, Dict]:
    """Load all games from the database directory."""
    database_dir = 'database'
    all_data = {}
    
    if not os.path.exists(database_dir):
        print(f"[ERROR] Database directory '{database_dir}' not found!")
        return {}
    
    # Load all _all.json files (these have all games for each console)
    for root, dirs, files in os.walk(database_dir):
        for file in files:
            if file.endswith('_all.json'):
                console_name = file.replace('_all.json', '')
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    games = json.load(f)
                    all_data[console_name] = {
                        'games': games,
                        'count': len(games)
                    }
    
    return all_data


def generate_css() -> str:
    """Generate CSS styles with dark mode support."""
    return """/* Game Database Site Styles with Dark Mode */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    /* Light mode colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e9ecef;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --accent: #0d6efd;
    --accent-hover: #0b5ed7;
    --border: #dee2e6;
    --shadow: rgba(0, 0, 0, 0.1);
    --shadow-hover: rgba(0, 0, 0, 0.15);
}

@media (prefers-color-scheme: dark) {
    :root {
        /* Dark mode colors */
        --bg-primary: #1a1a1a;
        --bg-secondary: #2d2d2d;
        --bg-tertiary: #3a3a3a;
        --text-primary: #e0e0e0;
        --text-secondary: #a0a0a0;
        --accent: #4a9eff;
        --accent-hover: #6ab0ff;
        --border: #404040;
        --shadow: rgba(0, 0, 0, 0.3);
        --shadow-hover: rgba(0, 0, 0, 0.4);
    }
}

[data-theme="light"] {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e9ecef;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --accent: #0d6efd;
    --accent-hover: #0b5ed7;
    --border: #dee2e6;
    --shadow: rgba(0, 0, 0, 0.1);
    --shadow-hover: rgba(0, 0, 0, 0.15);
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --bg-tertiary: #3a3a3a;
    --text-primary: #e0e0e0;
    --text-secondary: #a0a0a0;
    --accent: #4a9eff;
    --accent-hover: #6ab0ff;
    --border: #404040;
    --shadow: rgba(0, 0, 0, 0.3);
    --shadow-hover: rgba(0, 0, 0, 0.4);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    line-height: 1.6;
    font-size: 16px;
}

header {
    background-color: var(--bg-primary);
    border-bottom: 2px solid var(--border);
    padding: 2rem 0;
    margin-bottom: 3rem;
    box-shadow: 0 2px 4px var(--shadow);
}

.header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
    position: relative;
}

header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    display: inline-block;
}

.theme-toggle {
    position: absolute;
    top: 2rem;
    right: 2rem;
    background: none;
    border: 2px solid var(--accent);
    color: var(--accent);
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.2s;
}

.theme-toggle:hover {
    background-color: var(--accent);
    color: white;
}

@media (max-width: 768px) {
    .theme-toggle {
        position: static;
        margin-top: 1rem;
        display: block;
    }
}

header p {
    color: var(--text-secondary);
    font-size: 1.1rem;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem 4rem;
}

.stats-bar {
    background-color: var(--bg-primary);
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px var(--shadow);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    display: block;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

.search-section {
    margin-bottom: 2rem;
}

.search-box {
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    border: 2px solid var(--border);
    border-radius: 8px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
}

.console-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.console-card {
    background-color: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    display: block;
}

.console-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px var(--shadow-hover);
    border-color: var(--accent);
}

.console-card h2 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.console-card .console-count {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.games-table {
    width: 100%;
    background-color: var(--bg-primary);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px var(--shadow);
    margin-bottom: 2rem;
}

.games-table table {
    width: 100%;
    border-collapse: collapse;
}

.games-table thead {
    background-color: var(--bg-tertiary);
}

.games-table th {
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--border);
}

.games-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
}

.games-table tbody tr:hover {
    background-color: var(--bg-secondary);
}

.games-table tbody tr:last-child td {
    border-bottom: none;
}

.pagination {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 2rem;
}

.page-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
}

.page-btn:hover {
    background-color: var(--bg-secondary);
    border-color: var(--accent);
}

.page-btn.active {
    background-color: var(--accent);
    color: white;
    border-color: var(--accent);
}

.page-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.filter-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.filter-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
}

.filter-btn:hover {
    background-color: var(--bg-secondary);
    border-color: var(--accent);
}

.filter-btn.active {
    background-color: var(--accent);
    color: white;
    border-color: var(--accent);
}

.hidden {
    display: none;
}

.back-link {
    display: inline-block;
    margin-bottom: 1.5rem;
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.back-link:hover {
    color: var(--accent-hover);
}

.footer {
    background-color: var(--bg-primary);
    border-top: 2px solid var(--border);
    padding: 2rem 0;
    margin-top: 4rem;
    text-align: center;
    color: var(--text-secondary);
}

@media (max-width: 768px) {
    header h1 {
        font-size: 2rem;
    }
    
    .console-grid {
        grid-template-columns: 1fr;
    }
    
    .games-table {
        font-size: 0.9rem;
    }
    
    .games-table th,
    .games-table td {
        padding: 0.5rem;
    }
}
"""


def generate_js() -> str:
    """Generate JavaScript for interactivity."""
    return """// Game Database Site JavaScript
(function() {
    'use strict';
    
    let allGames = {};
    let currentConsole = null;
    let filteredGames = [];
    let currentPage = 1;
    const gamesPerPage = 50;
    
    // Common game acronyms and search shortcuts
    const searchShortcuts = {
        'gta': ['grand theft auto'],
        'cod': ['call of duty'],
        'mw': ['modern warfare'],
        'battlefield': ['battlefield'],
        'bf': ['battlefield'],
        'halo': ['halo'],
        'mario': ['mario'],
        'zelda': ['legend of zelda', 'zelda'],
        'pokemon': ['pokemon', 'pokémon'],
        'ff': ['final fantasy'],
        'mgs': ['metal gear solid'],
        'assassins creed': ['assassins creed'],
        'resident evil': ['resident evil'],
        're': ['resident evil'],
        'mk': ['mortal kombat'],
        'sf': ['street fighter'],
        'tekken': ['tekken'],
        'persona': ['persona'],
        'doom': ['doom'],
        'witcher': ['witcher'],
        'fallout': ['fallout'],
        'skyrim': ['skyrim'],
        'dark souls': ['dark souls'],
        'cs': ['counter-strike'],
        'rockstar': ['rockstar'],
        'bethesda': ['bethesda'],
        'nintendo': ['nintendo'],
        'sony': ['sony'],
        'microsoft': ['microsoft'],
        'ea': ['electronic arts'],
        'activision': ['activision'],
        'ubisoft': ['ubisoft'],
        'capcom': ['capcom'],
        'konami': ['konami'],
        'square': ['square'],
        'square enix': ['square enix'],
        'namco': ['namco'],
        'bandai': ['bandai'],
        'sega': ['sega'],
        'atari': ['atari'],
        'thq': ['thq']
    };
    
    function expandSearchQuery(query) {
        // Expand search shortcuts to full search terms
        const normalizedQuery = query.toLowerCase().trim();
        
        // Check if query matches a shortcut
        if (searchShortcuts[normalizedQuery]) {
            return searchShortcuts[normalizedQuery];
        }
        
        // Return original query if no shortcut found
        return [normalizedQuery];
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Initialize theme toggle
        initThemeToggle();
        
        // Load game data from embedded JSON (only on console page)
        const dataScript = document.getElementById('games-data');
        if (dataScript) {
            try {
                allGames = JSON.parse(dataScript.textContent);
            } catch (e) {
                console.error('Failed to parse game data:', e);
            }
        }
        
        // Setup homepage (console selection page)
        if (document.querySelector('.console-grid')) {
            setupConsolePage();
        }
        
        // Setup console page (games list page)
        if (document.getElementById('console-name')) {
            setupGamesPage();
        }
    }
    
    function initThemeToggle() {
        // Get saved theme or use system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        } else if (prefersDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
        
        // Setup theme toggle button
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            updateThemeToggleText();
            themeToggle.addEventListener('click', function() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeToggleText();
            });
        }
    }
    
    function updateThemeToggleText() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            themeToggle.textContent = currentTheme === 'dark' ? '☀️ Light' : '🌙 Dark';
        }
    }
    
    function normalizeText(text) {
        // Normalize accented and special characters to ASCII equivalents
        return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    
    function setupConsolePage() {
        // Add click handlers to console cards (already links, but ensure they work)
        const cards = document.querySelectorAll('.console-card');
        
        // Setup search on main page (filter console cards)
        const searchBox = document.getElementById('search-box');
        if (searchBox) {
            searchBox.addEventListener('input', function() {
                const rawQuery = this.value.toLowerCase().trim();
                const query = normalizeText(rawQuery);
                const cards = document.querySelectorAll('.console-card');
                
                cards.forEach(card => {
                    const name = normalizeText(card.querySelector('h2').textContent.toLowerCase());
                    const count = card.querySelector('.console-count').textContent;
                    
                    if (query === '' || name.includes(query) || count.includes(query)) {
                        card.classList.remove('hidden');
                        card.style.display = '';
                    } else {
                        card.classList.add('hidden');
                        card.style.display = 'none';
                    }
                });
            });
        }
    }
    
    function setupGamesPage() {
        const urlParams = new URLSearchParams(window.location.search);
        currentConsole = urlParams.get('console');
        
        if (!currentConsole || !allGames[currentConsole]) {
            document.getElementById('games-container').innerHTML = 
                '<p>Console not found. <a href="index.html">Return to home</a></p>';
            return;
        }
        
        filteredGames = allGames[currentConsole].games || [];
        renderGames();
        
        // Setup search for games page
        const searchBox = document.getElementById('search-box');
        if (searchBox) {
            searchBox.addEventListener('input', handleSearch);
        }
    }
    
    function handleSearch() {
        const rawQuery = document.getElementById('search-box').value.toLowerCase().trim();
        const query = normalizeText(rawQuery);
        
        if (!currentConsole || !allGames[currentConsole]) return;
        
        if (query === '') {
            filteredGames = allGames[currentConsole].games || [];
        } else {
            // Expand search shortcuts
            const searchTerms = expandSearchQuery(rawQuery);
            
            filteredGames = (allGames[currentConsole].games || []).filter(game => {
                const title = normalizeText((game.title || '').toLowerCase());
                const developer = normalizeText((game.developer || '').toLowerCase());
                const publisher = normalizeText((game.publisher || '').toLowerCase());
                
                // Check if any search term matches
                return searchTerms.some(term => {
                    const normalizedTerm = normalizeText(term.toLowerCase());
                    return title.includes(normalizedTerm) || 
                           developer.includes(normalizedTerm) || 
                           publisher.includes(normalizedTerm);
                });
            });
        }
        
        currentPage = 1;
        renderGames();
    }
    
    function renderGames() {
        const container = document.getElementById('games-container');
        if (!container) return;
        
        const start = (currentPage - 1) * gamesPerPage;
        const end = start + gamesPerPage;
        const pageGames = filteredGames.slice(start, end);
        const totalPages = Math.ceil(filteredGames.length / gamesPerPage);
        
        // Render table
        let html = '<table class="games-table"><thead><tr>';
        html += '<th>Title</th><th>Developer</th><th>Publisher</th><th>Release</th>';
        html += '</tr></thead><tbody>';
        
        if (pageGames.length === 0) {
            html += '<tr><td colspan="4" style="text-align: center; padding: 2rem;">No games found</td></tr>';
        } else {
            pageGames.forEach(game => {
                html += '<tr>';
                html += `<td><strong>${escapeHtml(game.title || 'Unknown')}</strong></td>`;
                html += `<td>${escapeHtml(game.developer || '—')}</td>`;
                html += `<td>${escapeHtml(game.publisher || '—')}</td>`;
                
                // Find first release date
                let release = game.jp_release || game.na_release || game.pal_release || 
                             game.first_released || game.release || '—';
                html += `<td>${escapeHtml(release)}</td>`;
                html += '</tr>';
            });
        }
        
        html += '</tbody></table>';
        
        // Render pagination
        if (totalPages > 1) {
            html += '<div class="pagination">';
            html += `<button class="page-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
            
            for (let i = 1; i <= totalPages; i++) {
                if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
                } else if (i === currentPage - 3 || i === currentPage + 3) {
                    html += '<button class="page-btn" disabled>...</button>';
                }
            }
            
            html += `<button class="page-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
            html += '</div>';
        }
        
        html += `<p style="text-align: center; margin-top: 1rem; color: var(--text-secondary);">Showing ${start + 1}-${Math.min(end, filteredGames.length)} of ${filteredGames.length} games</p>`;
        
        container.innerHTML = html;
    }
    
    function changePage(page) {
        const totalPages = Math.ceil(filteredGames.length / gamesPerPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderGames();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Make changePage globally available
    window.changePage = changePage;
})();
"""


def generate_index_html(all_data: Dict[str, Dict]) -> str:
    """Generate the main index page."""
    total_consoles = len(all_data)
    total_games = sum(data['count'] for data in all_data.values())
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EOL Console Games</title>
    <style>{generate_css()}</style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>EOL Console Games</h1>
            <p>Comprehensive database of games from discontinued consoles that have reached End of Life</p>
            <button id="theme-toggle" class="theme-toggle">🌙 Dark</button>
        </div>
    </header>
    
    <main>
        <div class="stats-bar">
            <div class="stat-item">
                <span class="stat-number">{total_consoles}</span>
                <span class="stat-label">Consoles</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{total_games:,}</span>
                <span class="stat-label">Total Games</span>
            </div>
        </div>
        
        <div class="search-section">
            <input type="text" id="search-box" class="search-box" placeholder="Search consoles...">
        </div>
        
        <div class="console-grid">
"""
    
    # Sort consoles by game count (descending)
    sorted_consoles = sorted(all_data.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for console_name, data in sorted_consoles:
        console_display = console_name.upper().replace('_', ' ')
        count = data['count']
        html_content += f"""            <a href="console.html?console={console_name}" class="console-card" data-console="{console_name}">
                <h2>{html.escape(console_display)}</h2>
                <div class="console-count">{count:,} games</div>
            </a>
"""
    
    html_content += """        </div>
    </main>
    
    <footer class="footer">
        <p>EOL Console Games &copy; 2025 | Created by Aspenini | Data extracted from Wikipedia</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
    
    return html_content


def generate_console_html(all_data: Dict[str, Dict]) -> str:
    """Generate console-specific page with progressive enhancement."""
    # Generate JSON data string first (escape script tags)
    json_data = json.dumps(all_data, ensure_ascii=False).replace('</script>', '<\\/script>')
    
    # Sort consoles by game count
    sorted_consoles = sorted(all_data.items(), key=lambda x: x[1]['count'], reverse=True)
    
    # Build noscript console links
    noscript_consoles = ""
    for console_name, data in sorted_consoles:
        console_display = console_name.upper().replace('_', ' ')
        noscript_consoles += f"""                    <a href="console.html?console={console_name}" class="console-card">
                        <h2>{html.escape(console_display)}</h2>
                        <div class="console-count">{data['count']:,} games</div>
                    </a>
"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Console Games - EOL Console Games</title>
    <style>{generate_css()}</style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1 id="console-name">Select a Console</h1>
            <p>Browse games by console</p>
            <button id="theme-toggle" class="theme-toggle">🌙 Dark</button>
        </div>
    </header>
    
    <main>
        <noscript>
            <div style="background-color: var(--bg-primary); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; border: 2px solid var(--accent);">
                <p style="margin-bottom: 1rem;"><strong>JavaScript is disabled</strong></p>
                <p style="color: var(--text-secondary);">This page works better with JavaScript enabled. Here are all available consoles:</p>
                <div class="console-grid" style="margin-top: 1.5rem;">
{noscript_consoles}                </div>
            </div>
        </noscript>
        
        <a href="index.html" class="back-link">← Back to Consoles</a>
        
        <div class="search-section">
            <input type="text" id="search-box" class="search-box" placeholder="Search games by title, developer, or publisher...">
        </div>
        
        <div id="games-container">
            <p>Please enable JavaScript to view games, or select a console from the list above.</p>
        </div>
    </main>
    
    <footer class="footer">
        <p>EOL Console Games &copy; 2025 | Created by Aspenini | Data extracted from Wikipedia</p>
    </footer>
    
    <script id="games-data" type="application/json">{json_data}</script>
    <script>{generate_js()}</script>
    <script>
        // Update console name in header and show appropriate section
        const urlParams = new URLSearchParams(window.location.search);
        const console = urlParams.get('console');
        if (console) {{
            const consoleName = console.toUpperCase().replace(/_/g, ' ');
            document.getElementById('console-name').textContent = consoleName;
            document.title = consoleName + ' - EOL Console Games';
        }}
    </script>
</body>
</html>"""
    
    return html_content


def main():
    """Main function to build the static site."""
    print("Building static website...")
    
    # Load all game data
    print("Loading game data...")
    all_data = load_all_games()
    
    if not all_data:
        print("[ERROR] No game data found!")
        return
    
    print(f"Loaded {len(all_data)} consoles with {sum(d['count'] for d in all_data.values()):,} total games")
    
    # Create site directory
    site_dir = 'site'
    if os.path.exists(site_dir):
        import shutil
        shutil.rmtree(site_dir)
    os.makedirs(site_dir)
    
    # Generate index page
    print("Generating index page...")
    index_html = generate_index_html(all_data)
    with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Generate console page
    print("Generating console page...")
    console_html = generate_console_html(all_data)
    with open(os.path.join(site_dir, 'console.html'), 'w', encoding='utf-8') as f:
        f.write(console_html)
    
    # Generate standalone CSS file
    print("Generating CSS file...")
    with open(os.path.join(site_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(generate_css())
    
    # Generate standalone JS file
    print("Generating JavaScript file...")
    with open(os.path.join(site_dir, 'script.js'), 'w', encoding='utf-8') as f:
        f.write(generate_js())
    
    print(f"\n[SUCCESS] Site built successfully in '{site_dir}/' directory")
    print(f"Open '{site_dir}/index.html' in your browser to view the site")


if __name__ == '__main__':
    # Set UTF-8 encoding for Windows console
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    main()
