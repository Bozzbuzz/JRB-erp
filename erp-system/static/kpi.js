// Global State
let rawData = [];
let filteredData = [];
let charts = {};
let kpiStartDate = null;
let kpiEndDate = null;

// Expose date filter for custom date picker component
window.applyClientDateFilter = (start, end) => {
    kpiStartDate = start;
    kpiEndDate = end;
    applyFilters();
};

// Helper: Format Currency (IDR)
const formatIDR = (value) => {
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value || 0);
};

// Helper: Format Date
const formatDate = (dateObj) => {
    if (!dateObj) return '';
    return dateObj.toISOString().slice(0, 7); // YYYY-MM
};

// Load Data from Flask Backend API
async function loadData() {
    try {
        const response = await fetch('/api/kpi-data');
        if (!response.ok) throw new Error('Gagal memuat data');
        
        const res = await response.json();
        rawData = res.data.map(row => ({
            ...row,
            bookDate: row.bookDate ? new Date(row.bookDate) : null,
            monthYear: row.bookDate ? row.bookDate.substring(0, 7) : ''
        }));
        
        filteredData = [...rawData];
        
        initFilters();
        applyFilters();
        
        // Hide loading
        const loadingDiv = document.getElementById('kpi-loading');
        if (loadingDiv) {
            loadingDiv.style.opacity = '0';
            setTimeout(() => loadingDiv.style.display = 'none', 500);
        }
    } catch (error) {
        console.error('Error loading KPI data:', error);
        alert('Gagal mengambil data dari database. Pastikan Flask server berjalan dengan benar.');
    }
}

// Initialize Filters
function initFilters() {
    const types = [...new Set(rawData.map(d => d.type).filter(Boolean))].sort();
    const marketings = [...new Set(rawData.map(d => d.marketing).filter(Boolean))].sort();
    const destinations = [...new Set(rawData.map(d => d.destination).filter(Boolean))].sort();

    const populateSelect = (id, options, formatter = null) => {
        const select = document.getElementById(id);
        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }
        options.forEach(opt => {
            const el = document.createElement('option');
            el.value = opt;
            el.textContent = formatter ? formatter(opt) : opt;
            select.appendChild(el);
        });
    };

    populateSelect('filter-type', types);
    populateSelect('filter-marketing', marketings);
    populateSelect('filter-destination', destinations);

    // Event Listeners
    document.getElementById('filter-type').addEventListener('change', applyFilters);
    document.getElementById('filter-marketing').addEventListener('change', applyFilters);
    document.getElementById('filter-destination').addEventListener('change', applyFilters);
    
    document.getElementById('btn-reset').addEventListener('click', () => {
        kpiStartDate = null;
        kpiEndDate = null;
        const dateText = document.getElementById('customDateText');
        if (dateText) dateText.innerText = 'Semua Waktu';
        document.getElementById('filter-type').value = '';
        document.getElementById('filter-marketing').value = '';
        document.getElementById('filter-destination').value = '';
        applyFilters();
    });
}

// Apply Filters
function applyFilters() {
    const type = document.getElementById('filter-type').value;
    const marketing = document.getElementById('filter-marketing').value;
    const destination = document.getElementById('filter-destination').value;

    filteredData = rawData.filter(row => {
        let match = true;
        if (kpiStartDate && row.bookDate && row.bookDate < new Date(kpiStartDate)) match = false;
        if (kpiEndDate && row.bookDate && row.bookDate > new Date(kpiEndDate + 'T23:59:59')) match = false;
        if (type && row.type !== type) match = false;
        if (marketing && row.marketing !== marketing) match = false;
        if (destination && row.destination !== destination) match = false;
        return match;
    });

    const infoText = (kpiStartDate && kpiEndDate) ? `Data periode ${kpiStartDate} - ${kpiEndDate}` : 'Menampilkan seluruh data';
    document.getElementById('last-updated-text').textContent = infoText + ` (${filteredData.length} transaksi)`;

    updateDashboard();
}

// Update KPI & Charts
function updateDashboard() {
    // 1. Calculate KPIs
    const totalSell = filteredData.reduce((sum, row) => sum + row.totalSell, 0);
    const totalBuy = filteredData.reduce((sum, row) => sum + row.totalBuy, 0);
    const profit = totalSell - totalBuy;
    const totalQty = filteredData.reduce((sum, row) => sum + row.qtySell, 0);

    // Update DOM
    document.getElementById('kpi-sales').textContent = formatIDR(totalSell);
    document.getElementById('kpi-buying').textContent = formatIDR(totalBuy);
    
    const profitEl = document.getElementById('kpi-profit');
    profitEl.textContent = formatIDR(profit);
    if (profit < 0) {
        profitEl.className = 'font-headline-lg text-red-600 relative z-10 font-bold text-xl';
    } else {
        profitEl.className = 'font-headline-lg text-green-700 relative z-10 font-bold text-xl';
    }
    
    document.getElementById('kpi-qty').textContent = totalQty.toLocaleString('id-ID');

    // 2. Update Charts
    updateTrendChart();
    updateMarketingChart();
}

// Update Trend Chart
function updateTrendChart() {
    const trendMap = {};
    filteredData.forEach(row => {
        if (!row.monthYear) return;
        if (!trendMap[row.monthYear]) {
            trendMap[row.monthYear] = { sales: 0, profit: 0 };
        }
        trendMap[row.monthYear].sales += row.totalSell;
        trendMap[row.monthYear].profit += (row.totalSell - row.totalBuy);
    });

    const sortedMonths = Object.keys(trendMap).sort();
    const salesData = sortedMonths.map(m => trendMap[m].sales);
    const profitData = sortedMonths.map(m => trendMap[m].profit);

    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (charts.trend) charts.trend.destroy();

    Chart.defaults.color = '#75777f';
    
    charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedMonths,
            datasets: [
                {
                    label: 'Total Penjualan',
                    data: salesData,
                    borderColor: '#031636', // primary color
                    backgroundColor: 'rgba(3, 22, 54, 0.05)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Profit',
                    data: profitData,
                    borderColor: '#2c694e', // secondary color
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { font: { family: 'Inter' } } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatIDR(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rp ' + (value / 1000000).toFixed(0) + 'M';
                        },
                        font: { family: 'Inter' }
                    },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter' } }
                }
            }
        }
    });
}

// Update Marketing Chart
function updateMarketingChart() {
    const marketingMap = {};
    filteredData.forEach(row => {
        if (row.marketing === 'Unknown') return;
        marketingMap[row.marketing] = (marketingMap[row.marketing] || 0) + row.totalSell;
    });

    const topMarketing = Object.entries(marketingMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    const labels = topMarketing.map(t => t[0]);
    const data = topMarketing.map(t => t[1]);

    const ctx = document.getElementById('marketingChart').getContext('2d');
    
    if (charts.marketing) charts.marketing.destroy();

    charts.marketing = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Penjualan',
                data: data,
                backgroundColor: [
                    'rgba(3, 22, 54, 0.85)',
                    'rgba(44, 105, 78, 0.85)',
                    'rgba(186, 26, 26, 0.85)',
                    'rgba(26, 43, 76, 0.85)',
                    'rgba(130, 147, 186, 0.85)'
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatIDR(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rp ' + (value / 1000000).toFixed(0) + 'M';
                        },
                        font: { family: 'Inter' }
                    },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter' } }
                }
            }
        }
    });
}

// Start
window.onload = loadData;
