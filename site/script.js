// Game Database Site JavaScript
(function() {
    'use strict';
    
    let allGames = {};
    let currentConsole = null;
    let filteredGames = [];
    let currentPage = 1;
    const gamesPerPage = 50;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Load game data from embedded JSON
        const dataScript = document.getElementById('games-data');
        if (dataScript) {
            try {
                allGames = JSON.parse(dataScript.textContent);
                setupConsolePage();
            } catch (e) {
                console.error('Failed to parse game data:', e);
            }
        }
        
        // Setup search functionality
        const searchBox = document.getElementById('search-box');
        if (searchBox) {
            searchBox.addEventListener('input', handleSearch);
        }
        
        // Setup console page
        if (document.getElementById('console-name')) {
            setupGamesPage();
        }
    }
    
    function setupConsolePage() {
        // Add click handlers to console cards
        const cards = document.querySelectorAll('.console-card');
        cards.forEach(card => {
            card.addEventListener('click', function(e) {
                e.preventDefault();
                const console = this.dataset.console;
                window.location.href = `console.html?console=${console}`;
            });
        });
        
        // Setup search on main page
        const searchBox = document.getElementById('search-box');
        if (searchBox) {
            searchBox.addEventListener('input', function() {
                const query = this.value.toLowerCase().trim();
                const cards = document.querySelectorAll('.console-card');
                
                cards.forEach(card => {
                    const name = card.querySelector('h2').textContent.toLowerCase();
                    const count = card.querySelector('.console-count').textContent;
                    
                    if (query === '' || name.includes(query) || count.includes(query)) {
                        card.classList.remove('hidden');
                    } else {
                        card.classList.add('hidden');
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
    }
    
    function handleSearch() {
        const query = document.getElementById('search-box').value.toLowerCase().trim();
        
        if (!currentConsole || !allGames[currentConsole]) return;
        
        if (query === '') {
            filteredGames = allGames[currentConsole].games || [];
        } else {
            filteredGames = (allGames[currentConsole].games || []).filter(game => {
                const title = (game.title || '').toLowerCase();
                const developer = (game.developer || '').toLowerCase();
                const publisher = (game.publisher || '').toLowerCase();
                return title.includes(query) || developer.includes(query) || publisher.includes(query);
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
