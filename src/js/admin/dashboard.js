// Admin Dashboard JavaScript
class AdminDashboard {
    constructor() {
        this.apiBaseUrl = '/admin/api';

        // Authentication and permissions
        this.authToken = null;
        this.currentAdmin = null;
        this.loginUrl = '/auth/login?type=admin';
        this.isAuthenticated = false;

        this.init();
    }

    async init() {
        // Check authentication first
        const authResult = await this.checkAuthentication();
        if (!authResult) {
            this.redirectToLogin('You need to log in to access the admin dashboard');
            return;
        }

        await this.loadDashboardData();
        this.setupCharts();
        this.setupEventListeners();
    }

    async checkAuthentication() {
        try {
            this.authToken = this.getAuthToken();

            if (!this.authToken) {
                console.log('No auth token found');
                return false;
            }

            // Verify token with backend - using admin profile endpoint
            const response = await fetch('/admin/api/profile/', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.status === 401 || response.status === 403) {
                console.log('Authentication failed');
                this.clearAuthData();
                return false;
            }

            if (response.ok) {
                this.currentAdmin = await response.json();
                this.isAuthenticated = true;
                return true;
            }

            return false;
        } catch (error) {
            console.error('Authentication check failed:', error);
            return false;
        }
    }

    checkPermission(action) {
        if (!this.isAuthenticated) {
            this.redirectToLogin('Authentication required');
            return false;
        }

        // Check if admin account is active
        if (this.currentAdmin && this.currentAdmin.user && this.currentAdmin.user.status !== 'active') {
            this.showNotification('Your account is not active. Please contact support.', 'error');
            return false;
        }

        // Admin permissions based on access level
        const adminActions = [
            'view_dashboard', 'manage_users', 'manage_drivers', 'view_trips',
            'view_analytics', 'manage_payments', 'view_profile'
        ];

        const superuserActions = [
            'delete_users', 'manage_admins', 'system_settings'
        ];

        if (adminActions.includes(action)) {
            return true;
        }

        if (superuserActions.includes(action)) {
            if (this.currentAdmin && this.currentAdmin.access_level === 'superuser') {
                return true;
            }
            this.showNotification('Superuser access required for this action', 'error');
            return false;
        }

        this.showNotification('You do not have permission to perform this action', 'error');
        return false;
    }

    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.isAuthenticated) {
            this.redirectToLogin('Authentication required');
            return null;
        }

        const defaultHeaders = {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json'
        };

        const requestOptions = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, requestOptions);

            if (response.status === 401) {
                this.handleAuthenticationError('Session expired. Please log in again.');
                return null;
            }

            if (response.status === 403) {
                this.showNotification('You do not have permission to perform this action', 'error');
                return null;
            }

            return response;
        } catch (error) {
            console.error('API request failed:', error);
            this.showNotification('Network error. Please check your connection.', 'error');
            return null;
        }
    }

    handleAuthenticationError(message) {
        this.clearAuthData();
        this.showNotification(message, 'error');
        setTimeout(() => {
            this.redirectToLogin(message);
        }, 2000);
    }

    redirectToLogin(message = 'Please log in to continue') {
        const currentUrl = encodeURIComponent(window.location.pathname + window.location.search);
        const loginUrl = `${this.loginUrl}&redirect=${currentUrl}&message=${encodeURIComponent(message)}`;
        window.location.href = loginUrl;
    }

    clearAuthData() {
        localStorage.removeItem('authToken');
        sessionStorage.removeItem('authToken');
        this.authToken = null;
        this.currentAdmin = null;
        this.isAuthenticated = false;
    }

    async loadDashboardData() {
        if (!this.checkPermission('view_dashboard')) return;

        try {
            const response = await this.makeAuthenticatedRequest(`${this.apiBaseUrl}/analytics/dashboard`);

            if (response && response.ok) {
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
        if (!this.checkPermission('manage_users')) return [];

        try {
            const response = await this.makeAuthenticatedRequest(
                `${this.apiBaseUrl}/users?skip=${(page - 1) * limit}&limit=${limit}`
            );

            if (response && response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
        return [];
    }

    async loadDrivers(status = null, page = 1, limit = 10) {
        if (!this.checkPermission('manage_drivers')) return [];

        let url = `${this.apiBaseUrl}/drivers?skip=${(page - 1) * limit}&limit=${limit}`;
        if (status) {
            url += `&approval_status=${status}`;
        }

        try {
            const response = await this.makeAuthenticatedRequest(url);

            if (response && response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error loading drivers:', error);
        }
        return [];
    }

    async approveDriver(userId, approved = true) {
        if (!this.checkPermission('manage_drivers')) return false;

        try {
            const response = await this.makeAuthenticatedRequest(
                `${this.apiBaseUrl}/drivers/${userId}/approval`,
                {
                    method: 'PUT',
                    body: JSON.stringify({
                        approval_status: approved ? 'approved' : 'rejected'
                    })
                }
            );

            return response && response.ok;
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
