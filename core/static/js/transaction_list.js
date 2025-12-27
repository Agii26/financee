/**
 * ============================================
 * TRANSACTION_LIST.JS - FinanceHub Transactions
 * ============================================
 * Handles all transaction list functionality:
 * - Filtering and sorting
 * - Pagination
 * - Modal details
 * - Export to CSV
 * - Print functionality
 * - Category breakdown chart
 * ============================================
 */

// ============================================
// GLOBAL STATE
// ============================================
let currentFilters = {
    datePreset: 'this_month',
    dateFrom: null,
    dateTo: null,
    transactionType: '',
    category: '',
    minAmount: null,
    maxAmount: null,
    search: '',
    sortBy: '-date',
    page: 1
};

let allTransactions = [];
let filteredTransactions = [];

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Format number as Philippine Peso
 */
function formatCurrency(amount) {
    return '₱' + parseFloat(amount).toLocaleString('en-PH', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Get date range based on preset
 */
function getDateRangeFromPreset(preset) {
    const today = new Date();
    const startOfDay = new Date(today.setHours(0, 0, 0, 0));
    let from, to;

    switch(preset) {
        case 'today':
            from = startOfDay;
            to = new Date();
            break;
        case 'this_week':
            const dayOfWeek = today.getDay();
            const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
            from = new Date(today.setDate(diff));
            from.setHours(0, 0, 0, 0);
            to = new Date();
            break;
        case 'this_month':
            from = new Date(today.getFullYear(), today.getMonth(), 1);
            to = new Date();
            break;
        case 'last_month':
            from = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            to = new Date(today.getFullYear(), today.getMonth(), 0);
            break;
        case 'this_year':
            from = new Date(today.getFullYear(), 0, 1);
            to = new Date();
            break;
        default:
            return { from: null, to: null };
    }

    return { from, to };
}

// ============================================
// FILTER FUNCTIONS
// ============================================

/**
 * Apply all filters to transactions
 */
function applyFilters() {
    console.log('Applying filters:', currentFilters);
    console.log('Total transactions:', allTransactions.length);
    
    let filtered = [...allTransactions];

    // Date filter
    if (currentFilters.datePreset && currentFilters.datePreset !== 'custom') {
        const { from, to } = getDateRangeFromPreset(currentFilters.datePreset);
        if (from && to) {
            filtered = filtered.filter(t => {
                const tDate = new Date(t.date);
                return tDate >= from && tDate <= to;
            });
        }
    } else if (currentFilters.dateFrom || currentFilters.dateTo) {
        if (currentFilters.dateFrom) {
            const fromDate = new Date(currentFilters.dateFrom);
            filtered = filtered.filter(t => new Date(t.date) >= fromDate);
        }
        if (currentFilters.dateTo) {
            const toDate = new Date(currentFilters.dateTo);
            toDate.setHours(23, 59, 59, 999);
            filtered = filtered.filter(t => new Date(t.date) <= toDate);
        }
    }

    // Transaction type filter
    if (currentFilters.transactionType) {
        filtered = filtered.filter(t => t.transaction_type === currentFilters.transactionType);
    }

    // Category filter
    if (currentFilters.category) {
        filtered = filtered.filter(t => t.category.id == currentFilters.category);
    }

    // Amount range filter
    if (currentFilters.minAmount) {
        filtered = filtered.filter(t => parseFloat(t.amount) >= parseFloat(currentFilters.minAmount));
    }
    if (currentFilters.maxAmount) {
        filtered = filtered.filter(t => parseFloat(t.amount) <= parseFloat(currentFilters.maxAmount));
    }

    // Search filter
    if (currentFilters.search) {
        const searchLower = currentFilters.search.toLowerCase();
        filtered = filtered.filter(t => 
            t.title.toLowerCase().includes(searchLower) ||
            (t.description && t.description.toLowerCase().includes(searchLower))
        );
    }

    // Sort
    filtered = sortTransactions(filtered, currentFilters.sortBy);

    filteredTransactions = filtered;
    console.log('Filtered transactions:', filteredTransactions.length);
    
    updateUI();
}

/**
 * Sort transactions
 */
function sortTransactions(transactions, sortBy) {
    const sorted = [...transactions];
    
    switch(sortBy) {
        case '-date':
            sorted.sort((a, b) => new Date(b.date) - new Date(a.date));
            break;
        case 'date':
            sorted.sort((a, b) => new Date(a.date) - new Date(b.date));
            break;
        case '-amount':
            sorted.sort((a, b) => parseFloat(b.amount) - parseFloat(a.amount));
            break;
        case 'amount':
            sorted.sort((a, b) => parseFloat(a.amount) - parseFloat(b.amount));
            break;
        case 'category':
            sorted.sort((a, b) => a.category.name.localeCompare(b.category.name));
            break;
        case 'transaction_type':
            sorted.sort((a, b) => a.transaction_type.localeCompare(b.transaction_type));
            break;
    }
    
    return sorted;
}

/**
 * Clear all filters
 */
function clearFilters() {
    document.getElementById('filterForm').reset();
    document.getElementById('datePreset').value = 'this_month';
    currentFilters = {
        datePreset: 'this_month',
        dateFrom: null,
        dateTo: null,
        transactionType: '',
        category: '',
        minAmount: null,
        maxAmount: null,
        search: '',
        sortBy: currentFilters.sortBy,
        page: 1
    };
    applyFilters();
}

// ============================================
// UI UPDATE FUNCTIONS
// ============================================

/**
 * Update all UI elements
 */
function updateUI() {
    updateTransactionsList();
    updateSummaryCards();
    updateCategoryChart();
    updatePagination();
    updateResultCount();
}

/**
 * Update transactions list display
 */
function updateTransactionsList() {
    const container = document.getElementById('transactionsList');
    if (!container) return;

    const perPage = 50;
    const start = (currentFilters.page - 1) * perPage;
    const end = start + perPage;
    const pageTransactions = filteredTransactions.slice(start, end);

    if (pageTransactions.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="empty-state-large">
                    <i class="fas fa-receipt"></i>
                    <h4>No Transactions Found</h4>
                    <p>No transactions match your current filters.</p>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = pageTransactions.map(transaction => `
        <div class="col-12">
            <div class="transaction-card" data-transaction-id="${transaction.id}" onclick="showTransactionDetails(${transaction.id})">
                <div class="transaction-card-body">
                    <div class="transaction-icon-wrapper">
                        <div class="transaction-icon ${
                            transaction.transaction_type === 'income' ? 'bg-success' : 
                            transaction.transaction_type === 'expense' ? 'bg-danger' : 
                            'bg-info'
                        }">
                            <i class="fas fa-${
                                transaction.transaction_type === 'income' ? 'arrow-up' : 
                                transaction.transaction_type === 'expense' ? 'arrow-down' : 
                                'piggy-bank'
                            }"></i>
                        </div>
                    </div>
                    
                    <div class="transaction-details">
                        <h6 class="transaction-title">${transaction.title}</h6>
                        <div class="transaction-meta">
                            <span class="category-badge" style="background: ${transaction.category.color}"></span>
                            <span>${transaction.category.name}</span>
                            <span class="mx-2">•</span>
                            <span>${formatDate(transaction.date)}</span>
                            ${transaction.description ? `
                                <span class="mx-2">•</span>
                                <span class="text-muted">${transaction.description.substring(0, 50)}${transaction.description.length > 50 ? '...' : ''}</span>
                            ` : ''}
                        </div>
                    </div>

                    <div class="transaction-amount-wrapper">
                        <div class="transaction-amount ${
                            transaction.transaction_type === 'income' ? 'text-success' : 
                            transaction.transaction_type === 'expense' ? 'text-danger' : 
                            'text-info'
                        }">
                            ${transaction.transaction_type === 'income' ? '+' : transaction.transaction_type === 'expense' ? '-' : ''}${formatCurrency(transaction.amount)}
                        </div>
                        <span class="badge ${
                            transaction.transaction_type === 'income' ? 'bg-success' : 
                            transaction.transaction_type === 'expense' ? 'bg-danger' : 
                            'bg-info'
                        }">
                            ${transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)}
                        </span>
                    </div>

                    <div class="transaction-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); showTransactionDetails(${transaction.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Update summary cards
 */
function updateSummaryCards() {
    const income = filteredTransactions
        .filter(t => t.transaction_type === 'income')
        .reduce((sum, t) => sum + parseFloat(t.amount), 0);
    
    const expenses = filteredTransactions
        .filter(t => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + parseFloat(t.amount), 0);
    
    const savings = filteredTransactions
        .filter(t => t.transaction_type === 'savings')
        .reduce((sum, t) => sum + parseFloat(t.amount), 0);
    
    const netBalance = income - expenses;

    document.getElementById('totalIncome').textContent = formatCurrency(income);
    document.getElementById('totalExpenses').textContent = formatCurrency(expenses);
    document.getElementById('totalSavings').textContent = formatCurrency(savings);
    document.getElementById('netBalance').textContent = formatCurrency(netBalance);
}

/**
 * Update result count
 */
function updateResultCount() {
    const countElement = document.getElementById('resultCount');
    if (countElement) {
        countElement.textContent = filteredTransactions.length;
    }
}

/**
 * Update pagination
 */
function updatePagination() {
    const nav = document.getElementById('paginationNav');
    if (!nav) return;

    const totalPages = Math.ceil(filteredTransactions.length / 50);
    
    if (totalPages <= 1) {
        nav.innerHTML = '';
        return;
    }

    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentFilters.page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentFilters.page - 1}); return false;">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentFilters.page - 2 && i <= currentFilters.page + 2)) {
            html += `
                <li class="page-item ${i === currentFilters.page ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentFilters.page - 3 || i === currentFilters.page + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    // Next button
    html += `
        <li class="page-item ${currentFilters.page === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentFilters.page + 1}); return false;">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;

    nav.innerHTML = html;
}

/**
 * Change page
 */
function changePage(page) {
    const totalPages = Math.ceil(filteredTransactions.length / 50);
    if (page < 1 || page > totalPages) return;
    
    currentFilters.page = page;
    updateTransactionsList();
    updatePagination();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================
// CATEGORY CHART
// ============================================

let categoryChartInstance = null;

/**
 * Initialize and update category breakdown chart
 */
function updateCategoryChart() {
    const canvas = document.getElementById('categoryChart');
    if (!canvas) return;

    // Calculate category breakdown from filtered transactions
    const categoryTotals = {};
    filteredTransactions
        .filter(t => t.transaction_type === 'expense')
        .forEach(t => {
            if (!categoryTotals[t.category.id]) {
                categoryTotals[t.category.id] = {
                    name: t.category.name,
                    color: t.category.color,
                    total: 0
                };
            }
            categoryTotals[t.category.id].total += parseFloat(t.amount);
        });

    const categories = Object.values(categoryTotals).sort((a, b) => b.total - a.total);
    const totalExpenses = categories.reduce((sum, cat) => sum + cat.total, 0);

    // Update legend
    updateCategoryLegend(categories, totalExpenses);

    // Destroy existing chart
    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    // Create new chart
    const ctx = canvas.getContext('2d');
    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.total),
                backgroundColor: categories.map(c => c.color),
                borderColor: '#2d2d2d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#2d2d2d',
                    titleColor: '#f8f9fa',
                    bodyColor: '#f8f9fa',
                    borderColor: '#6f42c1',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const percentage = ((context.parsed / totalExpenses) * 100).toFixed(1);
                            return context.label + ': ' + formatCurrency(context.parsed) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update category legend
 */
function updateCategoryLegend(categories, totalExpenses) {
    const legend = document.getElementById('categoryLegend');
    if (!legend) return;

    if (categories.length === 0) {
        legend.innerHTML = '<p class="text-muted text-center">No expense data available</p>';
        return;
    }

    legend.innerHTML = categories.map(cat => {
        const percentage = ((cat.total / totalExpenses) * 100).toFixed(1);
        return `
            <div class="category-legend-item">
                <div class="category-legend-color" style="background: ${cat.color}"></div>
                <div class="category-legend-name">${cat.name}</div>
                <div class="category-legend-amount">${formatCurrency(cat.total)}</div>
                <div class="category-legend-percentage">${percentage}%</div>
            </div>
        `;
    }).join('');
}

// ============================================
// TRANSACTION DETAILS MODAL
// ============================================

/**
 * Show transaction details in modal
 */
function showTransactionDetails(transactionId) {
    const transaction = allTransactions.find(t => t.id === transactionId);
    if (!transaction) return;

    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    const content = document.getElementById('transactionDetailsContent');

    content.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Title</span>
            <span class="detail-value">${transaction.title}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Amount</span>
            <span class="detail-value large ${
                transaction.transaction_type === 'income' ? 'text-success' : 
                transaction.transaction_type === 'expense' ? 'text-danger' : 
                'text-info'
            }">
                ${transaction.transaction_type === 'income' ? '+' : transaction.transaction_type === 'expense' ? '-' : ''}${formatCurrency(transaction.amount)}
            </span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Type</span>
            <span class="detail-value">
                <span class="badge ${
                    transaction.transaction_type === 'income' ? 'bg-success' : 
                    transaction.transaction_type === 'expense' ? 'bg-danger' : 
                    'bg-info'
                }">
                    ${transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)}
                </span>
            </span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Category</span>
            <span class="detail-value">
                <span class="category-badge" style="background: ${transaction.category.color}"></span>
                ${transaction.category.name}
            </span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Date</span>
            <span class="detail-value">${formatDate(transaction.date)}</span>
        </div>
        ${transaction.description ? `
            <div class="detail-row">
                <span class="detail-label">Description</span>
                <span class="detail-value">${transaction.description}</span>
            </div>
        ` : ''}
    `;

    modal.show();
}

// ============================================
// EXPORT FUNCTIONS
// ============================================

/**
 * Export transactions to CSV
 */
function exportToCSV() {
    if (filteredTransactions.length === 0) {
        alert('No transactions to export');
        return;
    }

    const headers = ['Date', 'Title', 'Type', 'Category', 'Amount', 'Description'];
    const csvContent = [
        headers.join(','),
        ...filteredTransactions.map(t => [
            t.date,
            `"${t.title}"`,
            t.transaction_type,
            `"${t.category.name}"`,
            t.amount,
            `"${t.description || ''}"`
        ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Print transactions
 */
function printTransactions() {
    window.print();
}

// ============================================
// EVENT LISTENERS
// ============================================

/**
 * Initialize all event listeners
 */
function initEventListeners() {
    // Filter form submission - FIXED TO PREVENT BASE.HTML INTERFERENCE
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopImmediatePropagation(); // Stop the global form handler in base.html
            
            // Get the submit button
            const submitBtn = document.getElementById('applyFiltersBtn');
            const originalHTML = '<i class="fas fa-search me-1"></i>Apply';
            
            // Show loading state on button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Filtering...';
            }
            
            const formData = new FormData(filterForm);
            currentFilters.datePreset = formData.get('date_preset') || '';
            currentFilters.dateFrom = formData.get('date_from') || null;
            currentFilters.dateTo = formData.get('date_to') || null;
            currentFilters.transactionType = formData.get('transaction_type') || '';
            currentFilters.category = formData.get('category') || '';
            currentFilters.minAmount = formData.get('min_amount') || null;
            currentFilters.maxAmount = formData.get('max_amount') || null;
            currentFilters.search = formData.get('search') || '';
            currentFilters.page = 1;
            
            // Apply filters
            applyFilters();
            
            // Restore button state
            if (submitBtn) {
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHTML;
                }, 150);
            }
        }, true); // Use capture phase to run before global handler
    }

    // Clear filters button
    const clearBtn = document.getElementById('clearFilters');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearFilters);
    }

    // Date preset change
    const datePreset = document.getElementById('datePreset');
    if (datePreset) {
        datePreset.addEventListener('change', (e) => {
            const customRange = document.getElementById('customDateRange');
            const customRangeTo = document.getElementById('customDateRangeTo');
            
            if (e.target.value === 'custom') {
                customRange.style.display = 'block';
                customRangeTo.style.display = 'block';
            } else {
                customRange.style.display = 'none';
                customRangeTo.style.display = 'none';
            }
        });
    }

    // Sort change
    const sortBy = document.getElementById('sortBy');
    if (sortBy) {
        sortBy.addEventListener('change', (e) => {
            currentFilters.sortBy = e.target.value;
            currentFilters.page = 1;
            applyFilters();
        });
    }

    // Toggle filters
    const toggleBtn = document.getElementById('toggleFilters');
    const filterPanel = document.getElementById('filterPanel');
    if (toggleBtn && filterPanel) {
        toggleBtn.addEventListener('click', () => {
            const isHidden = filterPanel.style.display === 'none';
            filterPanel.style.display = isHidden ? 'block' : 'none';
            toggleBtn.innerHTML = isHidden 
                ? '<i class="fas fa-chevron-up me-1"></i>Hide Filters'
                : '<i class="fas fa-chevron-down me-1"></i>Show Filters';
        });
    }

    // Export button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }

    // Print button
    const printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', printTransactions);
    }
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize everything
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Transaction List initializing...');
    console.log('Window data:', window.transactionData);

    // Load transaction data
    if (window.transactionData && window.transactionData.transactions) {
        allTransactions = window.transactionData.transactions;
        filteredTransactions = [...allTransactions];
        console.log('Loaded transactions:', allTransactions.length);
    } else {
        console.error('No transaction data found!');
        console.log('Available window.transactionData:', window.transactionData);
    }

    // Initialize Chart.js if available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded!');
    }

    // Initialize event listeners
    initEventListeners();

    // Apply initial filters
    applyFilters();

    console.log('Transaction List initialized successfully');
});