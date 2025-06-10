// Admin Dashboard JavaScript
class AdminDashboard {
    constructor() {
        this.apiBaseUrl = '/admin/api';
        this.init();
    }

    async init() {
        await this.loadDashboardData();
        this.setupCharts();
        this.setupEventListeners();
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/analytics/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
            } else {
                console.error('Failed to load dashboard data');
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    updateDashboardStats(data) {
        // Update user stats
        document.querySelector('[data-stat="total-users"]').textContent =
            data.users?.total || 0;
        document.querySelector('[data-stat="total-drivers"]').textContent =
            data.users?.drivers || 0;
        document.querySelector('[data-stat="active-drivers"]').textContent =
            data.users?.active_drivers || 0;

        // Update trip stats
        document.querySelector('[data-stat="total-trips"]').textContent =
            data.trips?.total || 0;
        document.querySelector('[data-stat="completed-trips"]').textContent =
            data.trips?.completed || 0;
        document.querySelector('[data-stat="pending-trips"]').textContent =
            data.trips?.pending || 0;

        // Update revenue
        document.querySelector('[data-stat="total-revenue"]').textContent =
            `$${(data.revenue?.total || 0).toLocaleString()}`;
    }

    setupCharts() {
        // Trip status chart
        const tripStatusCtx = document.getElementById('tripStatusChart');
        if (tripStatusCtx) {
            this.createTripStatusChart(tripStatusCtx);
        }

        // Revenue chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            this.createRevenueChart(revenueCtx);
        }

        // Driver approval chart
        const driverCtx = document.getElementById('driverApprovalChart');
        if (driverCtx) {
            this.createDriverApprovalChart(driverCtx);
        }
    }

    createTripStatusChart(container) {
        const chart = echarts.init(container);

        const option = {
            title: {
                text: 'Trip Status Distribution',
                left: 'center'
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            series: [{
                name: 'Trip Status',
                type: 'pie',
                radius: '50%',
                data: [
                    { value: 0, name: 'Pending' },
                    { value: 0, name: 'In Progress' },
                    { value: 0, name: 'Completed' },
                    { value: 0, name: 'Cancelled' }
                ],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        };

        chart.setOption(option);
        this.tripStatusChart = chart;
    }

    createRevenueChart(container) {
        const chart = echarts.init(container);

        const option = {
            title: {
                text: 'Revenue Trend (Last 30 Days)',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: [] // Will be populated with actual dates
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    formatter: '${value}'
                }
            },
            series: [{
                name: 'Daily Revenue',
                type: 'line',
                data: [], // Will be populated with actual data
                smooth: true,
                lineStyle: {
                    color: '#5470c6'
                }
            }]
        };

        chart.setOption(option);
        this.revenueChart = chart;
    }

    createDriverApprovalChart(container) {
        const chart = echarts.init(container);

        const option = {
            title: {
                text: 'Driver Approval Status',
                left: 'center'
            },
            tooltip: {
                trigger: 'item'
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '18',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: [
                    { value: 0, name: 'Approved' },
                    { value: 0, name: 'Pending' },
                    { value: 0, name: 'Rejected' }
                ]
            }]
        };

        chart.setOption(option);
        this.driverApprovalChart = chart;
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData();
            });
        }

        // Auto refresh every 5 minutes
        setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);

        // Window resize handler for charts
        window.addEventListener('resize', () => {
            if (this.tripStatusChart) this.tripStatusChart.resize();
            if (this.revenueChart) this.revenueChart.resize();
            if (this.driverApprovalChart) this.driverApprovalChart.resize();
        });
    }

    getAuthToken() {
        // Try to get token from localStorage or cookie
        return localStorage.getItem('authToken') ||
               this.getCookie('authToken') || '';
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    async loadUsers(page = 1, limit = 10) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/users?skip=${(page - 1) * limit}&limit=${limit}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    }
                }
            );

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
        return [];
    }

    async loadDrivers(status = null, page = 1, limit = 10) {
        let url = `${this.apiBaseUrl}/drivers?skip=${(page - 1) * limit}&limit=${limit}`;
        if (status) {
            url += `&approval_status=${status}`;
        }

        try {
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error loading drivers:', error);
        }
        return [];
    }

    async approveDriver(userId, approved = true) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/drivers/${userId}/approval`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    },
                    body: JSON.stringify({
                        approval_status: approved ? 'approved' : 'rejected'
                    })
                }
            );

            return response.ok;
        } catch (error) {
            console.error('Error updating driver approval:', error);
            return false;
        }
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.classList.contains('admin-dashboard')) {
        window.adminDashboard = new AdminDashboard();
    }
});

// Utility functions
window.AdminUtils = {
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    formatDate: (dateString) => {
        return new Date(dateString).toLocaleDateString();
    },

    formatDateTime: (dateString) => {
        return new Date(dateString).toLocaleString();
    },

    confirmAction: (message, callback) => {
        if (confirm(message)) {
            callback();
        }
    }
};
