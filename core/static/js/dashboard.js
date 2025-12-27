/**
 * ============================================
 * DASHBOARD.JS - FinanceHub Dashboard
 * ============================================
 * Handles all dashboard functionality including:
 * - Chart initialization
 * - Quick expense form
 * - Real-time UI updates
 * - Error handling
 * ============================================
 */

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
 * Show alert notification in top-right corner
 */
function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alertContainer');
    const alertId = 'alert-' + Date.now();
    
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Update cash on hand display
 */
function updateCashOnHand(newAmount) {
    const cashElement = document.getElementById('cashOnHandValue');
    if (cashElement) {
        cashElement.textContent = formatCurrency(newAmount);
        
        // Update form data attribute
        const form = document.getElementById('quickExpenseForm');
        if (form) {
            form.setAttribute('data-cash-on-hand', newAmount);
        }
        
        // Update max hint text
        const maxHint = document.querySelector('.quick-expense-card .form-text');
        if (maxHint) {
            maxHint.textContent = `Max: ${formatCurrency(newAmount)}`;
        }
    }
}

/**
 * Update monthly expenses display
 */
function updateMonthlyExpenses(newAmount) {
    const expensesElement = document.getElementById('monthlyExpensesValue');
    if (expensesElement) {
        expensesElement.textContent = formatCurrency(newAmount);
    }
}

/**
 * Add new transaction to recent transactions list
 */
function addTransactionToList(transaction) {
    const transactionsList = document.getElementById('recentTransactionsList');
    if (!transactionsList) return;
    
    // Remove empty state if it exists
    const emptyState = transactionsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create transaction HTML
    const transactionHTML = `
        <div class="transaction-item" style="animation: slideInRight 0.3s ease;">
            <div class="d-flex justify-content-between align-items-start">
                <div class="d-flex align-items-start flex-grow-1">
                    <div class="me-3 mt-1">
                        <i class="fas fa-arrow-down text-danger fa-lg"></i>
                    </div>
                    <div>
                        <h6 class="mb-1">${transaction.title}</h6>
                        <small class="text-muted">
                            <span class="category-badge" style="background: ${transaction.category_color}"></span>
                            ${transaction.category_name} • ${transaction.date}
                        </small>
                    </div>
                </div>
                <div class="text-end ms-2">
                    <strong class="amount-negative">-${formatCurrency(transaction.amount)}</strong>
                </div>
            </div>
        </div>
    `;
    
    // Insert at the top
    transactionsList.insertAdjacentHTML('afterbegin', transactionHTML);
}

// ============================================
// CHART INITIALIZATION
// ============================================

/**
 * Initialize Expense Pie Chart
 */
function initExpensePieChart() {
    if (!window.dashboardData.hasCategoryExpenses) return;
    
    const pieCanvas = document.getElementById('expensePieChart');
    if (!pieCanvas) return;
    
    const ctx = pieCanvas.getContext('2d');
    const chartData = window.dashboardData.chartData;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: chartData.categories,
            datasets: [{
                data: chartData.amounts,
                backgroundColor: chartData.colors,
                borderColor: '#2d2d2d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#f8f9fa',
                        usePointStyle: true,
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: '#2d2d2d',
                    titleColor: '#f8f9fa',
                    bodyColor: '#f8f9fa',
                    borderColor: '#6f42c1',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + formatCurrency(context.parsed) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize Spending Trend Line Chart
 */
function initTrendLineChart() {
    const lineCanvas = document.getElementById('trendLineChart');
    if (!lineCanvas) return;
    
    const ctx = lineCanvas.getContext('2d');
    const monthlyTrend = window.dashboardData.monthlyTrend;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyTrend.map(item => item.month),
            datasets: [{
                label: 'Monthly Expenses',
                data: monthlyTrend.map(item => item.amount),
                borderColor: '#6f42c1',
                backgroundColor: 'rgba(111, 66, 193, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#6f42c1',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
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
                            return 'Expenses: ' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#adb5bd',
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    },
                    grid: {
                        color: '#404040'
                    }
                },
                x: {
                    ticks: {
                        color: '#adb5bd'
                    },
                    grid: {
                        color: '#404040'
                    }
                }
            }
        }
    });
}

// ============================================
// FORM VALIDATION
// ============================================

/**
 * Validate quick expense form
 */
function validateQuickExpenseForm(formData, cashOnHand) {
    const amount = parseFloat(formData.get('amount'));
    const category = formData.get('category');
    
    // Check if amount is provided
    if (!amount || amount <= 0) {
        showAlert('Please enter a valid amount', 'danger');
        return false;
    }
    
    // Check if category is selected
    if (!category) {
        showAlert('Please select a category', 'danger');
        return false;
    }
    
    // Check if amount exceeds cash on hand
    if (amount > cashOnHand) {
        showAlert(`Amount exceeds your available balance of ${formatCurrency(cashOnHand)}`, 'danger');
        return false;
    }
    
    return true;
}

// ============================================
// QUICK EXPENSE FORM HANDLER
// ============================================

/**
 * Handle quick expense form submission
 */
function initQuickExpenseForm() {
    const form = document.getElementById('quickExpenseForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalHTML = submitBtn.innerHTML;
        const cashOnHand = parseFloat(this.getAttribute('data-cash-on-hand'));
        
        // Validate form
        if (!validateQuickExpenseForm(formData, cashOnHand)) {
            return;
        }
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Adding...';
        
        try {
            const response = await fetch('/quick-expense/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Show success message
                showAlert(data.message || 'Expense added successfully!', 'success');
                
                // Reset form
                form.reset();
                
                // Update UI elements
                if (data.new_cash_on_hand !== undefined) {
                    updateCashOnHand(data.new_cash_on_hand);
                }
                
                if (data.new_monthly_expenses !== undefined) {
                    updateMonthlyExpenses(data.new_monthly_expenses);
                }
                
                // Add transaction to list
                if (data.transaction) {
                    addTransactionToList(data.transaction);
                }
                
            } else {
                // Handle validation errors from server
                showAlert(data.message || 'Failed to add expense. Please try again.', 'danger');
            }
            
        } catch (error) {
            console.error('Error:', error);
            showAlert('An error occurred. Please check your connection and try again.', 'danger');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;
        }
    });
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize all dashboard functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initialize charts
    if (typeof Chart !== 'undefined') {
        initExpensePieChart();
        initTrendLineChart();
    } else {
        console.error('Chart.js not loaded');
    }
    
    // Initialize quick expense form
    initQuickExpenseForm();
    
    // Auto-dismiss existing alerts
    setTimeout(() => {
        document.querySelectorAll('.alert:not(#alertContainer .alert)').forEach(alert => {
            if (alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
    
    console.log('Dashboard initialized successfully');
});