// Driver Dashboard JavaScript
class DriverDashboard {
    constructor() {
        this.map = null;
        this.driverMarker = null;
        this.isOnline = false;
        this.currentTrip = null;
        this.currentTripRequest = null;
        this.locationTracking = null;
        this.tripPolling = null;
        this.requestTimer = null;
        this.driverLocation = null;
        this.tripTimer = null;
        this.tripStartTime = null;

        // Authentication and permissions
        this.authToken = null;
        this.currentDriver = null;
        this.loginUrl = '/auth/login?type=driver';
        this.isAuthenticated = false;

        this.init();
    }

    async init() {
        // Check authentication first
        const authResult = await this.checkAuthentication();
        if (!authResult) {
            this.redirectToLogin('You need to log in to access the driver dashboard');
            return;
        }

        this.initializeMap();
        this.loadDriverData();
        this.loadRecentTrips();
        this.loadDriverStats();
        this.loadVehicleInfo();
        this.bindEvents();
        this.checkDriverLocation();

        // Check for active trip on page load
        this.checkActiveTrip();
    }

    initializeMap() {
        // Initialize Leaflet map
        this.map = L.map('map').setView([35.6892, 51.3890], 13); // Default to Tehran

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }

    checkDriverLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.driverLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.map.setView([this.driverLocation.lat, this.driverLocation.lng], 15);
                    this.updateDriverMarker();
                },
                (error) => {
                    console.error('Error getting location:', error);
                    this.showNotification('Unable to get your location. Please enable GPS.', 'warning');
                }
            );
        }
    }

    updateDriverMarker() {
        if (this.driverMarker) {
            this.map.removeLayer(this.driverMarker);
        }

        if (this.driverLocation) {
            this.driverMarker = L.marker([this.driverLocation.lat, this.driverLocation.lng], {
                icon: L.icon({
                    iconUrl: '/static/images/driver-marker.png',
                    iconSize: [30, 30],
                    iconAnchor: [15, 30]
                })
            }).addTo(this.map).bindPopup('Your Location');
        }
    }

    startLocationTracking() {
        if (navigator.geolocation) {
            this.locationTracking = navigator.geolocation.watchPosition(
                (position) => {
                    this.driverLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.updateDriverMarker();
                    this.sendLocationUpdate();
                },
                (error) => {
                    console.error('Error tracking location:', error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 30000
                }
            );
        }
    }

    stopLocationTracking() {
        if (this.locationTracking) {
            navigator.geolocation.clearWatch(this.locationTracking);
            this.locationTracking = null;
        }
    }

    async sendLocationUpdate() {
        if (!this.isOnline || !this.driverLocation) return;

        try {
            await fetch('/api/v1/drivers/location/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    latitude: this.driverLocation.lat,
                    longitude: this.driverLocation.lng
                })
            });
        } catch (error) {
            console.error('Error sending location update:', error);
        }
    }

    bindEvents() {
        // Online/Offline toggle
        document.getElementById('onlineToggle').addEventListener('change', (e) => {
            this.toggleOnlineStatus(e.target.checked);
        });

        // Trip request actions
        document.getElementById('acceptTripBtn')?.addEventListener('click', () => {
            this.acceptTripRequest();
        });

        document.getElementById('rejectTripBtn')?.addEventListener('click', () => {
            this.rejectTripRequest();
        });

        // Active trip actions
        document.getElementById('startTripBtn')?.addEventListener('click', () => {
            this.startTrip();
        });

        document.getElementById('completeTripBtn')?.addEventListener('click', () => {
            this.completeTrip();
        });

        document.getElementById('callPassengerBtn')?.addEventListener('click', () => {
            this.callPassenger();
        });

        document.getElementById('cancelTripDriverBtn')?.addEventListener('click', () => {
            this.cancelTrip();
        });

        // Issue reporting
        document.getElementById('reportIssueBtn')?.addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('issueModal'));
            modal.show();
        });

        document.getElementById('issueForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitIssueReport();
        });
    }

    async toggleOnlineStatus(online) {
        const action = online ? 'go_online' : 'go_offline';
        if (!this.checkPermission(action)) {
            document.getElementById('onlineToggle').checked = this.isOnline;
            return;
        }

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/status/', {
                method: 'POST',
                body: JSON.stringify({ is_online: online })
            });

            if (response && response.ok) {
                this.isOnline = online;
                this.updateOnlineUI();

                if (online) {
                    this.startLocationTracking();
                    this.startTripRequestPolling();
                    this.showNotification('You are now online and available for trips!', 'success');
                } else {
                    this.stopLocationTracking();
                    this.stopTripRequestPolling();
                    this.showNotification('You are now offline', 'info');
                }
            } else {
                document.getElementById('onlineToggle').checked = this.isOnline;
                this.showNotification('Failed to update status', 'error');
            }
        } catch (error) {
            document.getElementById('onlineToggle').checked = this.isOnline;
            console.error('Error toggling online status:', error);
            this.showNotification('Network error', 'error');
        }
    }

    updateOnlineUI() {
        const statusText = document.getElementById('onlineStatus');
        const statusCard = document.getElementById('statusCard');
        const onlineMessage = document.getElementById('onlineMessage');
        const offlineMessage = document.getElementById('offlineMessage');
        const statusTitle = document.getElementById('statusTitle');

        if (this.isOnline) {
            statusText.textContent = 'Online';
            statusText.className = 'form-check-label text-white';
            statusCard.querySelector('.card-header').className = 'card-header bg-success text-white';
            statusTitle.textContent = 'Online - Ready for Trips';
            onlineMessage.style.display = 'block';
            offlineMessage.style.display = 'none';
        } else {
            statusText.textContent = 'Offline';
            statusText.className = 'form-check-label text-white';
            statusCard.querySelector('.card-header').className = 'card-header bg-warning text-dark';
            statusTitle.textContent = 'Offline';
            onlineMessage.style.display = 'none';
            offlineMessage.style.display = 'block';
        }
    }

    startTripRequestPolling() {
        if (this.tripPolling) {
            clearInterval(this.tripPolling);
        }

        this.tripPolling = setInterval(() => {
            this.checkForTripRequests();
        }, 3000); // Check every 3 seconds
    }

    stopTripRequestPolling() {
        if (this.tripPolling) {
            clearInterval(this.tripPolling);
            this.tripPolling = null;
        }
    }

    async checkForTripRequests() {
        if (!this.isOnline || this.currentTripRequest || this.currentTrip) return;
        if (!this.checkPermission('accept_trip')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/available-trips/');

            if (response && response.ok) {
                const trips = await response.json();
                if (trips.length > 0) {
                    this.currentTripRequest = trips[0];
                    this.showTripRequest();
                }
            }
        } catch (error) {
            console.error('Error checking for trip requests:', error);
        }
    }

    showTripRequest() {
        const tripRequest = document.getElementById('tripRequest');
        const onlineMessage = document.getElementById('onlineMessage');

        onlineMessage.style.display = 'none';
        tripRequest.style.display = 'block';

        // Populate trip request details
        document.getElementById('requestPickup').textContent = this.currentTripRequest.pickup_address;
        document.getElementById('requestDestination').textContent = this.currentTripRequest.dropoff_address;
        document.getElementById('requestDistance').textContent = `${this.currentTripRequest.distance || 'N/A'} km`;
        document.getElementById('requestFare').textContent = `$${this.currentTripRequest.total_amount}`;
        document.getElementById('requestPassenger').textContent = this.currentTripRequest.user.first_name;
        document.getElementById('passengerRating').textContent = this.currentTripRequest.user.rating || '5.0';

        // Start countdown timer
        this.startRequestTimer();

        // Play notification sound (if available)
        this.playNotificationSound();

        // Show notification
        this.showNotification('New trip request received!', 'info');
    }

    startRequestTimer() {
        let timeLeft = 30;
        const timerElement = document.getElementById('requestTimer');

        this.requestTimer = setInterval(() => {
            timerElement.textContent = timeLeft;
            timeLeft--;

            if (timeLeft < 0) {
                this.rejectTripRequest();
            }
        }, 1000);
    }

    stopRequestTimer() {
        if (this.requestTimer) {
            clearInterval(this.requestTimer);
            this.requestTimer = null;
        }
    }

    async acceptTripRequest() {
        if (!this.currentTripRequest) return;
        if (!this.checkPermission('accept_trip')) return;

        this.stopRequestTimer();

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/drivers/trips/${this.currentTripRequest.id}/accept/`, {
                method: 'POST'
            });

            if (response && response.ok) {
                const trip = await response.json();
                this.currentTrip = trip;
                this.currentTripRequest = null;
                this.showActiveTrip();
                this.showNotification('Trip accepted! Navigate to pickup location.', 'success');
            } else if (response) {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to accept trip', 'error');
                this.hideTripRequest();
            }
        } catch (error) {
            console.error('Error accepting trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
            this.hideTripRequest();
        }
    }

    async rejectTripRequest() {
        if (!this.currentTripRequest) return;
        if (!this.checkPermission('reject_trip')) return;

        this.stopRequestTimer();

        try {
            await this.makeAuthenticatedRequest(`/api/v1/drivers/trips/${this.currentTripRequest.id}/reject/`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error rejecting trip:', error);
        }

        this.currentTripRequest = null;
        this.hideTripRequest();
    }

    hideTripRequest() {
        document.getElementById('tripRequest').style.display = 'none';
        if (this.isOnline) {
            document.getElementById('onlineMessage').style.display = 'block';
        }
    }

    showActiveTrip() {
        document.getElementById('tripRequest').style.display = 'none';
        document.getElementById('onlineMessage').style.display = 'none';
        document.getElementById('activeTrip').style.display = 'block';

        this.updateActiveTripUI();
        this.showTripOnMap();
        this.startTripTimer();
    }

    updateActiveTripUI() {
        if (!this.currentTrip) return;

        // Update passenger info
        document.getElementById('passengerName').textContent = this.currentTrip.user.first_name;
        document.getElementById('passengerPhone').textContent = this.currentTrip.user.phone;
        document.getElementById('passengerRatingActive').textContent = this.currentTrip.user.rating || '5.0';

        // Update trip details
        document.getElementById('activeTripPickup').textContent = this.currentTrip.pickup_address;
        document.getElementById('activeTripDestination').textContent = this.currentTrip.dropoff_address;
        document.getElementById('activeTripFare').textContent = `$${this.currentTrip.total_amount}`;

        // Update status and buttons
        const statusBadge = document.getElementById('activeTripStatus');
        const startBtn = document.getElementById('startTripBtn');
        const completeBtn = document.getElementById('completeTripBtn');

        switch (this.currentTrip.status) {
            case 'accepted':
                statusBadge.textContent = 'Heading to Pickup';
                statusBadge.className = 'badge bg-info';
                startBtn.style.display = 'block';
                completeBtn.style.display = 'none';
                break;

            case 'in_progress':
                statusBadge.textContent = 'In Progress';
                statusBadge.className = 'badge bg-success';
                startBtn.style.display = 'none';
                completeBtn.style.display = 'block';
                break;
        }
    }

    showTripOnMap() {
        if (!this.currentTrip) return;

        // Clear existing markers
        this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker && layer !== this.driverMarker) {
                this.map.removeLayer(layer);
            }
        });

        // Add pickup marker
        const pickupMarker = L.marker([
            this.currentTrip.pickup_latitude,
            this.currentTrip.pickup_longitude
        ], {
            icon: L.icon({
                iconUrl: '/static/images/pickup-marker.png',
                iconSize: [25, 25],
                iconAnchor: [12, 25]
            })
        }).addTo(this.map).bindPopup('Pickup Location');

        // Add dropoff marker
        const dropoffMarker = L.marker([
            this.currentTrip.dropoff_latitude,
            this.currentTrip.dropoff_longitude
        ], {
            icon: L.icon({
                iconUrl: '/static/images/dropoff-marker.png',
                iconSize: [25, 25],
                iconAnchor: [12, 25]
            })
        }).addTo(this.map).bindPopup('Dropoff Location');

        // Draw route
        const routeLine = L.polyline([
            [this.currentTrip.pickup_latitude, this.currentTrip.pickup_longitude],
            [this.currentTrip.dropoff_latitude, this.currentTrip.dropoff_longitude]
        ], {color: 'blue', weight: 4}).addTo(this.map);

        // Fit map to show all markers
        const allMarkers = [this.driverMarker, pickupMarker, dropoffMarker];
        const group = new L.featureGroup(allMarkers.concat([routeLine]));
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    startTripTimer() {
        this.tripStartTime = new Date();

        this.tripTimer = setInterval(() => {
            const now = new Date();
            const elapsed = Math.floor((now - this.tripStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;

            document.getElementById('tripDuration').textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTripTimer() {
        if (this.tripTimer) {
            clearInterval(this.tripTimer);
            this.tripTimer = null;
        }
    }

    async startTrip() {
        if (!this.currentTrip) return;
        if (!this.checkPermission('start_trip')) return;

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/drivers/trips/${this.currentTrip.id}/start/`, {
                method: 'POST'
            });

            if (response && response.ok) {
                this.currentTrip.status = 'in_progress';
                this.updateActiveTripUI();
                this.showNotification('Trip started! Drive safely to destination.', 'success');
            } else {
                this.showNotification('Failed to start trip', 'error');
            }
        } catch (error) {
            console.error('Error starting trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async completeTrip() {
        if (!this.currentTrip) return;
        if (!this.checkPermission('complete_trip')) return;

        if (!confirm('Are you sure you want to complete this trip?')) {
            return;
        }

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/drivers/trips/${this.currentTrip.id}/complete/`, {
                method: 'POST'
            });

            if (response && response.ok) {
                const completedTrip = await response.json();
                this.showTripCompletion(completedTrip);
                this.resetToOnlineState();
                this.loadTodayEarnings();
                this.loadRecentTrips();
            } else {
                this.showNotification('Failed to complete trip', 'error');
            }
        } catch (error) {
            console.error('Error completing trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    showTripCompletion(trip) {
        // Update modal with trip details
        document.getElementById('completedTripFare').textContent = `$${trip.total_amount}`;
        document.getElementById('completedTripDistance').textContent = `${trip.distance || 'N/A'} km`;

        // Show completion modal
        const modal = new bootstrap.Modal(document.getElementById('tripCompletionModal'));
        modal.show();

        this.showNotification('Trip completed successfully!', 'success');
    }

    async cancelTrip() {
        if (!this.currentTrip) return;
        if (!this.checkPermission('cancel_trip')) return;

        const reason = prompt('Please provide a reason for cancelling this trip:');
        if (!reason) return;

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/drivers/trips/${this.currentTrip.id}/cancel/`, {
                method: 'POST',
                body: JSON.stringify({
                    reason: reason
                })
            });

            if (response && response.ok) {
                this.showNotification('Trip cancelled', 'warning');
                this.resetToOnlineState();
            } else {
                this.showNotification('Failed to cancel trip', 'error');
            }
        } catch (error) {
            console.error('Error cancelling trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    callPassenger() {
        if (this.currentTrip && this.currentTrip.user) {
            window.open(`tel:${this.currentTrip.user.phone}`);
        }
    }

    resetToOnlineState() {
        this.currentTrip = null;
        this.stopTripTimer();

        document.getElementById('activeTrip').style.display = 'none';
        if (this.isOnline) {
            document.getElementById('onlineMessage').style.display = 'block';
        }

        // Clear map markers except driver marker
        this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker && layer !== this.driverMarker) {
                this.map.removeLayer(layer);
            }
            if (layer instanceof L.Polyline) {
                this.map.removeLayer(layer);
            }
        });
    }

    async checkActiveTrip() {
        if (!this.checkPermission('view_trips')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/trips/active/');

            if (response && response.ok) {
                const trip = await response.json();
                if (trip) {
                    this.currentTrip = trip;
                    this.isOnline = true;
                    document.getElementById('onlineToggle').checked = true;
                    this.updateOnlineUI();
                    this.showActiveTrip();
                    this.startLocationTracking();
                }
            }
        } catch (error) {
            console.error('Error checking active trip:', error);
        }
    }

    async loadDriverData() {
        if (!this.checkPermission('view_profile')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/profile/');

            if (response && response.ok) {
                const driverData = await response.json();
                this.currentDriver = driverData;
                document.getElementById('driverName').textContent = driverData.user.first_name;

                // Update driver status
                this.isOnline = driverData.is_active || false;
                document.getElementById('onlineToggle').checked = this.isOnline;
                this.updateOnlineUI();

                if (this.isOnline) {
                    this.startLocationTracking();
                    this.startTripRequestPolling();
                }
            }
        } catch (error) {
            console.error('Error loading driver data:', error);
        }
    }

    async loadRecentTrips() {
        if (!this.checkPermission('view_trips')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/trips/?limit=5');

            if (response && response.ok) {
                const trips = await response.json();
                this.displayRecentTrips(trips);
            }
        } catch (error) {
            console.error('Error loading recent trips:', error);
        }
    }

    displayRecentTrips(trips) {
        const container = document.getElementById('recentTrips');
        container.innerHTML = '';

        trips.forEach(trip => {
            const tripElement = document.createElement('div');
            tripElement.className = 'list-group-item list-group-item-action';
            tripElement.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${trip.pickup_address}</h6>
                    <small class="text-muted">${new Date(trip.created_at).toLocaleDateString()}</small>
                </div>
                <p class="mb-1 text-muted">${trip.dropoff_address}</p>
                <div class="d-flex justify-content-between">
                    <small class="text-success">$${trip.total_amount}</small>
                    <span class="badge bg-${this.getStatusColor(trip.status)}">${trip.status}</span>
                </div>
            `;
            container.appendChild(tripElement);
        });
    }

    async loadDriverStats() {
        if (!this.checkPermission('view_earnings')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/stats/');

            if (response && response.ok) {
                const stats = await response.json();
                document.querySelector('[data-stat="total-trips"]').textContent = stats.total_trips || 0;
                document.querySelector('[data-stat="total-earnings"]').textContent = `$${stats.total_earnings || 0}`;
                document.querySelector('[data-stat="avg-rating"]').textContent = (stats.avg_rating || 0).toFixed(1);
            }
        } catch (error) {
            console.error('Error loading driver stats:', error);
        }
    }

    async loadTodayEarnings() {
        if (!this.checkPermission('view_earnings')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/earnings/today/');

            if (response && response.ok) {
                const earnings = await response.json();
                document.getElementById('todayEarnings').textContent = earnings.amount.toFixed(2);
            }
        } catch (error) {
            console.error('Error loading today earnings:', error);
        }
    }

    async loadVehicleInfo() {
        if (!this.checkPermission('view_profile')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/vehicle/');

            if (response && response.ok) {
                const vehicle = await response.json();
                document.getElementById('vehicleMake').textContent = vehicle.make || 'N/A';
                document.getElementById('vehicleModel').textContent = vehicle.model || 'N/A';
                document.getElementById('licensePlate').textContent = vehicle.license_plate || 'N/A';
            }
        } catch (error) {
            console.error('Error loading vehicle info:', error);
        }
    }

    async submitIssueReport() {
        if (!this.checkPermission('report_issue')) return;

        const issueType = document.getElementById('issueType').value;
        const description = document.getElementById('issueDescription').value;
        const isEmergency = document.getElementById('emergencyCheck').checked;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/drivers/issues/', {
                method: 'POST',
                body: JSON.stringify({
                    issue_type: issueType,
                    description: description,
                    is_emergency: isEmergency,
                    trip_id: this.currentTrip?.id || null
                })
            });

            if (response && response.ok) {
                this.showNotification('Issue reported successfully. Support will contact you soon.', 'success');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('issueModal'));
                modal.hide();

                // Reset form
                document.getElementById('issueForm').reset();
            } else {
                this.showNotification('Failed to report issue', 'error');
            }
        } catch (error) {
            console.error('Error reporting issue:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async updateLocation() {
        if (!this.checkPermission('update_location')) return;

        if (navigator.geolocation && this.isOnline) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    this.driverLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };

                    // Update location on server
                    try {
                        await this.makeAuthenticatedRequest('/api/v1/drivers/location/', {
                            method: 'POST',
                            body: JSON.stringify({
                                latitude: this.driverLocation.lat,
                                longitude: this.driverLocation.lng
                            })
                        });
                    } catch (error) {
                        console.error('Error updating location:', error);
                    }

                    this.updateDriverMarker();
                },
                (error) => {
                    console.error('Error getting location:', error);
                }
            );
        }
    }

    async checkAuthentication() {
        try {
            this.authToken = this.getAuthToken();

            if (!this.authToken) {
                console.log('No auth token found');
                return false;
            }

            // Verify token with backend
            const response = await fetch('/api/v1/drivers/profile/', {
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
                this.currentDriver = await response.json();
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

        // Check if driver account is active and approved
        if (this.currentDriver && this.currentDriver.user && this.currentDriver.user.status !== 'active') {
            this.showNotification('Your account is not active. Please contact support.', 'error');
            return false;
        }

        if (this.currentDriver && this.currentDriver.approval_status !== 'approved') {
            this.showNotification('Your driver account is not approved yet. Please wait for admin approval.', 'warning');
            return false;
        }

        // Driver permissions
        const driverActions = [
            'go_online', 'go_offline', 'accept_trip', 'reject_trip', 'start_trip',
            'complete_trip', 'cancel_trip', 'view_trips', 'view_earnings',
            'update_location', 'view_profile', 'report_issue'
        ];

        if (driverActions.includes(action)) {
            return true;
        }

        this.showNotification('You do not have permission to perform this action', 'error');
        return false;
    }

    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.checkPermission('api_access')) {
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
        this.currentDriver = null;
        this.isAuthenticated = false;
    }

    getAuthToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }

    showNotification(message, type = 'info') {
        // Create and show a toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    playNotificationSound() {
        // Play notification sound for trip requests
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.play().catch(e => console.log('Could not play notification sound'));
        } catch (error) {
            console.log('Notification sound not available');
        }
    }

    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'accepted': 'info',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DriverDashboard();
});
