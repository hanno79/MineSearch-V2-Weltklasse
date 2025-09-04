/**
 * Author: rahn
 * Datum: 27.08.2025
 * Version: 1.0
 * Beschreibung: Database Viewer JavaScript für Read-Only Tabellen-Ansicht
 */

// Database Viewer State
let databaseViewer = {
    currentTable: 'mines',
    currentPage: 1,
    pageLimit: 50,
    totalPages: 1,
    totalCount: 0,
    sortBy: null,
    sortOrder: 'asc',
    filterColumn: null,
    filterValue: null,
    columns: [],
    tables: [],
    categories: {},
    normalizedStructure: false
};

/**
 * Initialisiert den Database Viewer
 */
async function initializeDatabaseViewer() {
    console.log('🗂️ [DATABASE-VIEWER-DEBUG] Initialisiere Database Viewer...');
    
    try {
        // Lade verfügbare Tabellen
        console.log('🔄 [DATABASE-VIEWER-DEBUG] Loading available tables...');
        await loadDatabaseTables();
        
        // Lade Standard-Tabelle
        console.log('🔄 [DATABASE-VIEWER-DEBUG] Loading default table: mines...');
        await loadTableData('mines');
        
        // Event Listener für Tab-Wechsel
        console.log('🔄 [DATABASE-VIEWER-DEBUG] Setting up event listeners...');
        setupDatabaseEventListeners();
        
        console.log('✅ [DATABASE-VIEWER-DEBUG] Database Viewer vollständig initialisiert');
    } catch (error) {
        console.error('❌ [DATABASE-VIEWER-DEBUG] Fehler beim Initialisieren des Database Viewers:', error);
        showDatabaseError('Fehler beim Laden des Database Viewers');
    }
}

/**
 * Lädt verfügbare Tabellen vom Backend
 */
async function loadDatabaseTables() {
    try {
        const response = await fetch('/api/database/tables?' + new Date().getTime()); // Cache-Buster
        const data = await response.json();
        
        if (data.success) {
            databaseViewer.tables = data.tables;
            databaseViewer.categories = data.categories || {};
            databaseViewer.normalizedStructure = data.normalized_structure || false;
            
            updateTableCounts(data.tables);
            updateTableCategorization(data.tables, data.categories);
            console.log('✅ [DATABASE-VIEWER] Normalisierte Tabellenstruktur geladen:', data.categories);
        }
    } catch (error) {
        console.error('❌ Fehler beim Laden der Tabellen:', error);
    }
}

/**
 * Aktualisiert die Tabellen-Counts in der Navigation
 */
function updateTableCounts(tables) {
    console.log('🔄 [DATABASE-VIEWER] Updating table counts for', tables.length, 'tables');
    
    tables.forEach(table => {
        const countElement = document.getElementById(`count-${table.name}`);
        if (countElement) {
            countElement.textContent = `(${table.row_count})`;
            countElement.style.opacity = table.row_count > 0 ? '1' : '0.5';
            
            // Add category-based styling
            const button = countElement.closest('.database-tab-btn');
            if (button) {
                if (table.category === 'Normalized (NEW)') {
                    button.style.borderLeft = '3px solid #059669';
                } else if (table.category === 'Legacy System') {
                    button.style.borderLeft = '3px solid #6b7280';
                }
            }
            
            console.log(`✅ [DATABASE-VIEWER] Updated ${table.name}: ${table.row_count} rows`);
        } else {
            console.warn(`⚠️ [DATABASE-VIEWER] Count element not found: count-${table.name}`);
        }
    });
}

/**
 * Aktualisiert Tabellen-Kategorisierung basierend auf normalisierter Struktur
 */
function updateTableCategorization(tables, categories) {
    console.log('🏗️ [DATABASE-VIEWER] Updating table categorization with normalized structure');
    
    if (!categories || Object.keys(categories).length === 0) {
        console.log('⚠️ [DATABASE-VIEWER] No categories provided - using existing structure');
        return;
    }
    
    // Hole das Tabellen-Container-Element
    const tabsContainer = document.querySelector('.database-tabs');
    if (!tabsContainer) {
        console.error('❌ [DATABASE-VIEWER] Tabs container not found');
        return;
    }
    
    // Lösche bestehende dynamische Kategorien (behalte nur den ersten Legacy-Bereich)
    const existingGroups = tabsContainer.querySelectorAll('.tab-group');
    existingGroups.forEach((group, index) => {
        if (index > 0) { // Behalte nur die erste Gruppe (Legacy System)
            group.remove();
        }
    });
    
    // Füge neue kategorisierte Gruppen hinzu
    const categoryColors = {
        'Stammdaten': '#059669',      // Grün
        'Kerndaten': '#0ea5e9',       // Blau  
        'Beziehungen': '#8b5cf6',     // Violett
        'Feldwerte': '#f59e0b'        // Orange
    };
    
    const categoryIcons = {
        'Stammdaten': '📋',
        'Kerndaten': '⛏️', 
        'Beziehungen': '🔗',
        'Feldwerte': '💾'
    };
    
    // Erstelle Gruppen für jede Kategorie
    Object.entries(categories).forEach(([categoryName, tableNames]) => {
        if (tableNames && tableNames.length > 0) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'tab-group';
            
            // Kategorie-Header
            const headerH4 = document.createElement('h4');
            headerH4.style.cssText = `
                margin: 15px 0 5px 0; 
                font-size: 0.85rem; 
                color: ${categoryColors[categoryName] || '#666'}; 
                text-transform: uppercase; 
                font-weight: 600;
            `;
            headerH4.innerHTML = `${categoryIcons[categoryName] || '📁'} ${categoryName}`;
            groupDiv.appendChild(headerH4);
            
            // Buttons für jede Tabelle in dieser Kategorie
            tableNames.forEach(tableName => {
                // Finde Tabellen-Info aus der API-Response
                const tableInfo = tables.find(t => t.name === tableName);
                if (!tableInfo) {
                    console.warn(`⚠️ [DATABASE-VIEWER] Table info not found for: ${tableName}`);
                    return;
                }
                
                const button = document.createElement('button');
                button.className = 'database-tab-btn';
                button.dataset.table = tableName;
                
                // Icon basierend auf Tabellennamen
                let icon = '📊';
                if (tableName.includes('mine')) icon = '⛏️';
                else if (tableName.includes('company') || tableName.includes('companies')) icon = '🏢';
                else if (tableName.includes('country') || tableName.includes('countries')) icon = '🌍';
                else if (tableName.includes('commodity') || tableName.includes('commodities')) icon = '💎';
                else if (tableName.includes('source')) icon = '📚';
                else if (tableName.includes('search')) icon = '🔍';
                else if (tableName.includes('field')) icon = '💾';
                else if (tableName.includes('production')) icon = '⚖️';
                else if (tableName.includes('restoration')) icon = '🌱';
                
                // Benutzerfreundlicher Display-Name
                let displayName = tableName
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
                
                button.innerHTML = `
                    <span class="db-icon">${icon}</span>
                    ${displayName}
                    <span class="db-count" id="count-${tableName}">(${tableInfo.row_count || 0})</span>
                `;
                
                // Füge Kategorie-spezifische Stylings hinzu
                button.style.borderLeft = `3px solid ${categoryColors[categoryName] || '#666'}`;
                
                // Event Listener
                button.addEventListener('click', () => {
                    loadTableData(tableName, 1);
                });
                
                groupDiv.appendChild(button);
            });
            
            tabsContainer.appendChild(groupDiv);
        }
    });
    
    console.log('✅ [DATABASE-VIEWER] Table categorization updated with normalized structure');
}

/**
 * Lädt Daten einer spezifischen Tabelle
 */
async function loadTableData(tableName, page = 1) {
    console.log(`📊 Lade Tabelle: ${tableName}, Seite: ${page}`);
    
    // UI Updates
    databaseViewer.currentTable = tableName;
    databaseViewer.currentPage = page;
    
    showDatabaseLoading();
    updateActiveTableTab(tableName);
    
    try {
        // API Parameter
        const params = new URLSearchParams({
            page: page,
            limit: databaseViewer.pageLimit
        });
        
        if (databaseViewer.sortBy) {
            params.append('sort_by', databaseViewer.sortBy);
            params.append('sort_order', databaseViewer.sortOrder);
        }
        
        if (databaseViewer.filterColumn && databaseViewer.filterValue) {
            params.append('filter_column', databaseViewer.filterColumn);
            params.append('filter_value', databaseViewer.filterValue);
        }
        
        const response = await fetch(`/api/database/table/${tableName}?${params}`);
        const result = await response.json();
        
        // DEBUG: Erweiterte Logging für Datenbank-Viewer
        console.log(`🔍 [DATABASE-VIEWER-DEBUG] API Response for ${tableName}:`, {
            success: result.success,
            totalRows: result.success ? result.data.pagination.total_count : 'N/A',
            returnedRows: result.success ? result.data.rows.length : 'N/A',
            columns: result.success ? result.data.columns.length : 'N/A'
        });
        
        if (result.success) {
            // Update State
            databaseViewer.columns = result.data.columns;
            databaseViewer.totalCount = result.data.pagination.total_count;
            databaseViewer.totalPages = result.data.pagination.total_pages;
            
            console.log(`✅ [DATABASE-VIEWER-DEBUG] Rendering ${result.data.rows.length} rows with ${result.data.columns.length} columns`);
            
            // Render Table
            renderDatabaseTable(result.data);
            updateFilterColumns(result.data.columns);
            updatePagination(result.data.pagination);
            
            hideDatabaseLoading();
        } else {
            throw new Error(result.error || 'Fehler beim Laden der Daten');
        }
        
    } catch (error) {
        console.error(`❌ Fehler beim Laden von Tabelle ${tableName}:`, error);
        showDatabaseError(`Fehler beim Laden der Tabelle: ${error.message}`);
        hideDatabaseLoading();
    }
}

/**
 * Rendert die Datenbank-Tabelle
 */
function renderDatabaseTable(data) {
    console.log(`🎨 [DATABASE-VIEWER-DEBUG] renderDatabaseTable called with:`, {
        rowCount: data.rows.length,
        columnCount: data.columns.length,
        tableName: databaseViewer.currentTable
    });
    
    const thead = document.getElementById('database-table-head');
    const tbody = document.getElementById('database-table-body');
    
    if (!thead || !tbody) {
        console.error('❌ [DATABASE-VIEWER-DEBUG] Table elements not found!', {
            thead: !!thead,
            tbody: !!tbody
        });
        return;
    }
    
    // Clear existing content
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    if (data.rows.length === 0) {
        console.log('ℹ️ [DATABASE-VIEWER-DEBUG] No rows to render - showing empty message');
        tbody.innerHTML = `
            <tr>
                <td colspan="${data.columns.length}" style="text-align: center; padding: 40px; color: #666;">
                    Keine Daten in dieser Tabelle gefunden
                </td>
            </tr>
        `;
        return;
    }
    
    // Render Headers
    const headerRow = document.createElement('tr');
    data.columns.forEach(column => {
        const th = document.createElement('th');
        th.className = 'sortable-header';
        th.onclick = () => sortTableBy(column);
        
        // Sort indicator
        let sortIndicator = '';
        if (databaseViewer.sortBy === column) {
            sortIndicator = databaseViewer.sortOrder === 'asc' ? ' ↑' : ' ↓';
        }
        
        // Build header content without using innerHTML for dynamic values
        const headerContent = document.createElement('div');
        headerContent.className = 'header-content';
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'column-name';
        nameSpan.textContent = formatColumnName(column);
        
        const sortSpan = document.createElement('span');
        sortSpan.className = 'sort-indicator';
        sortSpan.textContent = sortIndicator;
        
        const typeSpan = document.createElement('span');
        typeSpan.className = 'column-type';
        typeSpan.textContent = data.column_types[column] || '';
        
        headerContent.appendChild(nameSpan);
        headerContent.appendChild(sortSpan);
        headerContent.appendChild(typeSpan);
        th.appendChild(headerContent);
        
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    
    // Render Rows
    data.rows.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.className = index % 2 === 0 ? 'even-row' : 'odd-row';
        
        data.columns.forEach(column => {
            const td = document.createElement('td');
            const value = row[column];
            
            const cell = formatCellValue(value, data.column_types[column]);
            if (cell && typeof cell === 'object' && cell.type === 'html') {
                td.innerHTML = cell.content;
            } else {
                td.textContent = cell && cell.content !== undefined ? cell.content : '';
            }
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    
    // Show table
    document.getElementById('database-table-wrapper').style.display = 'block';
}

/**
 * Formatiert Spaltennamen für bessere Lesbarkeit
 */
function formatColumnName(column) {
    return column
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Formatiert Zell-Werte basierend auf Datentyp
 */
function formatCellValue(value, columnType) {
    if (value === null || value === undefined) {
        return { type: 'html', content: '<span class="null-value">NULL</span>' };
    }
    
    // JSON Values
    if (typeof value === 'object' && value.type === 'json') {
        const safeJson = escapeHtml(JSON.stringify(value.parsed, null, 2));
        return {
            type: 'html',
            content: `
                <div class="json-cell">
                    <button class="json-toggle" onclick="toggleJsonDisplay(this)">
                        📄 JSON anzeigen
                    </button>
                    <div class="json-content" style="display: none;">
                        <pre>${safeJson}</pre>
                    </div>
                </div>
            `
        };
    }
    
    // DateTime Values
    if (columnType && columnType.toLowerCase().includes('datetime')) {
        if (typeof value === 'string') {
            try {
                const date = new Date(value);
                return {
                    type: 'html',
                    content: `
                        <span class="datetime-value" title="${escapeHtml(String(value))}">
                            ${escapeHtml(date.toLocaleString('de-DE'))}
                        </span>
                    `
                };
            } catch (e) {
                return { type: 'text', content: String(value) };
            }
        }
    }
    
    // Long text values
    const stringValue = String(value);
    if (stringValue.length > 100) {
        return {
            type: 'html',
            content: `
                <div class="long-text">
                    <span class="text-preview">${escapeHtml(stringValue.substring(0, 100))}...</span>
                    <button class="text-expand" onclick="toggleTextDisplay(this)">mehr</button>
                    <div class="text-full" style="display: none;">${escapeHtml(stringValue)}</div>
                </div>
            `
        };
    }
    
    // Regular values
    return { type: 'text', content: stringValue };
}

/**
 * Sortiert Tabelle nach Spalte
 */
function sortTableBy(column) {
    if (databaseViewer.sortBy === column) {
        // Toggle sort order
        databaseViewer.sortOrder = databaseViewer.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        databaseViewer.sortBy = column;
        databaseViewer.sortOrder = 'asc';
    }
    
    // Reload with new sort
    loadTableData(databaseViewer.currentTable, 1);
}

/**
 * Wendet Filter auf aktuelle Tabelle an
 */
function applyDatabaseFilter() {
    const filterColumn = document.getElementById('db-filter-column').value;
    const filterValue = document.getElementById('db-filter-value').value.trim();
    
    if (!filterColumn || !filterValue) {
        alert('Bitte Spalte und Wert für Filter auswählen');
        return;
    }
    
    databaseViewer.filterColumn = filterColumn;
    databaseViewer.filterValue = filterValue;
    
    // Reset to page 1 with filter
    loadTableData(databaseViewer.currentTable, 1);
}

/**
 * Löscht aktuelle Filter
 */
function clearDatabaseFilter() {
    databaseViewer.filterColumn = null;
    databaseViewer.filterValue = null;
    
    document.getElementById('db-filter-column').value = '';
    document.getElementById('db-filter-value').value = '';
    
    // Reload without filter
    loadTableData(databaseViewer.currentTable, 1);
}

/**
 * Aktualisiert Filter-Spalten Dropdown
 */
function updateFilterColumns(columns) {
    const select = document.getElementById('db-filter-column');
    select.innerHTML = '<option value="">Filter Spalte wählen</option>';
    
    columns.forEach(column => {
        const option = document.createElement('option');
        option.value = column;
        option.textContent = formatColumnName(column);
        if (column === databaseViewer.filterColumn) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    // Set filter value if exists
    if (databaseViewer.filterValue) {
        document.getElementById('db-filter-value').value = databaseViewer.filterValue;
    }
}

/**
 * Aktualisiert Pagination UI
 */
function updatePagination(pagination) {
    const paginationDiv = document.getElementById('database-pagination');
    const infoText = document.getElementById('pagination-info-text');
    const pagesDiv = document.getElementById('pagination-pages');
    
    if (pagination.total_count === 0) {
        paginationDiv.style.display = 'none';
        return;
    }
    
    // Show pagination
    paginationDiv.style.display = 'flex';
    
    // Update info text
    const start = ((pagination.page - 1) * pagination.limit) + 1;
    const end = Math.min(pagination.page * pagination.limit, pagination.total_count);
    infoText.textContent = `Zeige ${start}-${end} von ${pagination.total_count} Einträgen`;
    
    // Update page buttons
    pagesDiv.innerHTML = '';
    
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.total_pages, pagination.page + 2);
    
    if (startPage > 1) {
        pagesDiv.appendChild(createPageButton(1));
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'pagination-ellipsis';
            pagesDiv.appendChild(ellipsis);
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pagesDiv.appendChild(createPageButton(i, i === pagination.page));
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'pagination-ellipsis';
            pagesDiv.appendChild(ellipsis);
        }
        pagesDiv.appendChild(createPageButton(pagination.total_pages));
    }
    
    // Update prev/next buttons
    document.getElementById('pagination-prev').disabled = !pagination.has_prev;
    document.getElementById('pagination-next').disabled = !pagination.has_next;
}

/**
 * Erstellt Page Button
 */
function createPageButton(pageNum, isActive = false) {
    const button = document.createElement('button');
    button.className = `pagination-page ${isActive ? 'active' : ''}`;
    button.textContent = pageNum;
    button.onclick = () => goToPage(pageNum);
    return button;
}

/**
 * Navigation zu spezifischer Seite
 */
function goToPage(page) {
    if (page >= 1 && page <= databaseViewer.totalPages) {
        loadTableData(databaseViewer.currentTable, page);
    }
}

/**
 * Vorherige Seite
 */
function previousPage() {
    if (databaseViewer.currentPage > 1) {
        loadTableData(databaseViewer.currentTable, databaseViewer.currentPage - 1);
    }
}

/**
 * Nächste Seite
 */
function nextPage() {
    if (databaseViewer.currentPage < databaseViewer.totalPages) {
        loadTableData(databaseViewer.currentTable, databaseViewer.currentPage + 1);
    }
}

/**
 * Aktualisiert aktiven Tabellen-Tab
 */
function updateActiveTableTab(tableName) {
    // Remove active from all tabs
    document.querySelectorAll('.database-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active to current tab
    const activeTab = document.querySelector(`[data-table="${tableName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

/**
 * Aktualisiert aktuelle Tabelle
 */
function refreshCurrentTable() {
    console.log('🔄 [DATABASE-VIEWER] Refreshing current table and counts');
    
    // Erst Tabellen-Counts neu laden
    loadDatabaseTables().then(() => {
        // Dann aktuelle Tabelle neu laden
        loadTableData(databaseViewer.currentTable, databaseViewer.currentPage);
    });
}

/**
 * Exportiert aktuelle Tabelle als CSV
 */
function exportCurrentTable() {
    const params = new URLSearchParams();
    if (databaseViewer.filterColumn && databaseViewer.filterValue) {
        params.append('filter_column', databaseViewer.filterColumn);
        params.append('filter_value', databaseViewer.filterValue);
    }
    
    const url = `/api/database/export/${databaseViewer.currentTable}/csv?${params}`;
    window.open(url, '_blank');
}

/**
 * Event Listener Setup
 */
function setupDatabaseEventListeners() {
    // Tab-Buttons
    document.querySelectorAll('.database-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tableName = btn.dataset.table;
            loadTableData(tableName, 1);
        });
    });
    
    // Page Limit Change
    document.getElementById('db-page-limit').addEventListener('change', (e) => {
        databaseViewer.pageLimit = parseInt(e.target.value);
        loadTableData(databaseViewer.currentTable, 1);
    });
    
    // Filter on Enter
    document.getElementById('db-filter-value').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            applyDatabaseFilter();
        }
    });
}

/**
 * Zeigt Loading State
 */
function showDatabaseLoading() {
    document.getElementById('database-loading').style.display = 'block';
    document.getElementById('database-table-wrapper').style.display = 'none';
    document.getElementById('database-error').style.display = 'none';
    document.getElementById('database-pagination').style.display = 'none';
}

/**
 * Versteckt Loading State
 */
function hideDatabaseLoading() {
    document.getElementById('database-loading').style.display = 'none';
}

/**
 * Zeigt Error State
 */
function showDatabaseError(message) {
    document.getElementById('database-error').style.display = 'block';
    document.getElementById('database-error').querySelector('p').textContent = message;
    document.getElementById('database-table-wrapper').style.display = 'none';
    document.getElementById('database-pagination').style.display = 'none';
}

/**
 * Toggle JSON Display
 */
function toggleJsonDisplay(button) {
    const content = button.nextElementSibling;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.textContent = '📄 JSON verstecken';
    } else {
        content.style.display = 'none';
        button.textContent = '📄 JSON anzeigen';
    }
}

/**
 * Toggle Text Display
 */
function toggleTextDisplay(button) {
    const preview = button.previousElementSibling;
    const full = button.nextElementSibling;
    
    if (full.style.display === 'none') {
        full.style.display = 'block';
        preview.style.display = 'none';
        button.textContent = 'weniger';
    } else {
        full.style.display = 'none';
        preview.style.display = 'inline';
        button.textContent = 'mehr';
    }
}

/**
 * HTML Escaping
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when database tab is loaded
if (typeof window !== 'undefined') {
    window.databaseViewer = {
        initialize: initializeDatabaseViewer,
        loadTable: loadTableData,
        refresh: refreshCurrentTable,
        export: exportCurrentTable
    };
}