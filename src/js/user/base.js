// User Dashboard JavaScript
class UserDashboard {
    constructor() {
        this.map = null;
        this.pickupMarker = null;
        this.dropoffMarker = null;
        this.routeControl = null;
        this.currentTrip = null;
        this.tripPolling = null;
        this.userLocation = null;
        this.selectedRating = 0;

        // Authentication and permissions
        this.authToken = null;
        this.currentUser = null;
        this.loginUrl = '/auth/login?type=user';
        this.isAuthenticated = false;

        this.init();
    }

    async init() {
        // Check authentication first
        const authResult = await this.checkAuthentication();
        if (!authResult) {
            this.redirectToLogin('You need to log in to access the user dashboard');
            return;
        }

        this.initializeMap();
        this.loadUserData();
        this.loadRecentTrips();
        this.loadUserStats();
        this.loadFavoriteLocations();
        this.bindEvents();
        this.getUserLocation();

        // Check for active trip on page load
        this.checkActiveTrip();
    }

    initializeMap() {
        // Initialize Leaflet map
        this.map = L.map('map').setView([35.6892, 51.3890], 13); // Default to Tehran

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add click handler for map
        this.map.on('click', (e) => {
            this.handleMapClick(e.latlng);
        });
    }

    getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.map.setView([this.userLocation.lat, this.userLocation.lng], 15);

                    // Add user location marker
                    L.marker([this.userLocation.lat, this.userLocation.lng])
                        .addTo(this.map)
                        .bindPopup('Your Location')
                        .openPopup();
                },
                (error) => {
                    console.error('Error getting location:', error);
                    this.showNotification('Unable to get your location', 'warning');
                }
            );
        }
    }

    handleMapClick(latlng) {
        const pickupInput = document.getElementById('pickupLocation');
        const dropoffInput = document.getElementById('dropoffLocation');

        // Determine which field is active/empty
        if (!pickupInput.value || pickupInput === document.activeElement) {
            this.setPickupLocation(latlng.lat, latlng.lng);
        } else if (!dropoffInput.value || dropoffInput === document.activeElement) {
            this.setDropoffLocation(latlng.lat, latlng.lng);
        }
    }

    setPickupLocation(lat, lng) {
        document.getElementById('pickupLat').value = lat;
        document.getElementById('pickupLng').value = lng;

        // Remove existing pickup marker
        if (this.pickupMarker) {
            this.map.removeLayer(this.pickupMarker);
        }

        // Add new pickup marker
        this.pickupMarker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: '/static/images/pickup-marker.png',
                iconSize: [25, 25],
                iconAnchor: [12, 25]
            })
        }).addTo(this.map);

        // Reverse geocode to get address
        this.reverseGeocode(lat, lng, 'pickupLocation');

        // Calculate fare if both locations are set
        this.calculateFare();
    }

    setDropoffLocation(lat, lng) {
        document.getElementById('dropoffLat').value = lat;
        document.getElementById('dropoffLng').value = lng;

        // Remove existing dropoff marker
        if (this.dropoffMarker) {
            this.map.removeLayer(this.dropoffMarker);
        }

        // Add new dropoff marker
        this.dropoffMarker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: '/static/images/dropoff-marker.png',
                iconSize: [25, 25],
                iconAnchor: [12, 25]
            })
        }).addTo(this.map);

        // Reverse geocode to get address
        this.reverseGeocode(lat, lng, 'dropoffLocation');

        // Calculate fare if both locations are set
        this.calculateFare();
    }

    reverseGeocode(lat, lng, inputId) {
        // Simple reverse geocoding (in real app, use a proper service)
        const address = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        document.getElementById(inputId).value = address;
    }

    calculateFare() {
        const pickupLat = document.getElementById('pickupLat').value;
        const pickupLng = document.getElementById('pickupLng').value;
        const dropoffLat = document.getElementById('dropoffLat').value;
        const dropoffLng = document.getElementById('dropoffLng').value;
        const tripType = document.getElementById('tripType').value;

        if (pickupLat && pickupLng && dropoffLat && dropoffLng) {
            // Calculate distance (simplified)
            const distance = this.calculateDistance(
                parseFloat(pickupLat), parseFloat(pickupLng),
                parseFloat(dropoffLat), parseFloat(dropoffLng)
            );

            // Calculate fare based on trip type
            let baseFare = 5.00;
            let perKmRate = 2.50;

            switch (tripType) {
                case 'premium':
                    baseFare = 8.00;
                    perKmRate = 3.50;
                    break;
                case 'shared':
                    baseFare = 3.00;
                    perKmRate = 1.80;
                    break;
            }

            const estimatedFare = baseFare + (distance * perKmRate);
            document.getElementById('estimatedFare').textContent = `$${estimatedFare.toFixed(2)}`;

            // Draw route on map
            this.drawRoute();
        }
    }

    calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371; // Earth's radius in km
        const dLat = this.toRadians(lat2 - lat1);
        const dLng = this.toRadians(lng2 - lng1);
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    toRadians(degrees) {
        return degrees * (Math.PI/180);
    }

    drawRoute() {
        if (this.routeControl) {
            this.map.removeControl(this.routeControl);
        }

        const pickupLat = parseFloat(document.getElementById('pickupLat').value);
        const pickupLng = parseFloat(document.getElementById('pickupLng').value);
        const dropoffLat = parseFloat(document.getElementById('dropoffLat').value);
        const dropoffLng = parseFloat(document.getElementById('dropoffLng').value);

        // Simple line (in real app, use routing service)
        const routeLine = L.polyline([
            [pickupLat, pickupLng],
            [dropoffLat, dropoffLng]
        ], {color: 'blue', weight: 4}).addTo(this.map);

        // Fit map to show both markers
        const group = new L.featureGroup([this.pickupMarker, this.dropoffMarker, routeLine]);
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    bindEvents() {
        // Booking form submission
        document.getElementById('bookingForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.bookRide();
        });

        // Trip type change
        document.getElementById('tripType').addEventListener('change', () => {
            this.calculateFare();
        });

        // Discount code application
        document.getElementById('applyDiscount').addEventListener('click', () => {
            this.applyDiscountCode();
        });

        // Wallet top-up form
        document.getElementById('topupForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.topupWallet();
        });

        // Trip actions
        document.getElementById('cancelTripBtn')?.addEventListener('click', () => {
            this.cancelTrip();
        });

        document.getElementById('callDriverBtn')?.addEventListener('click', () => {
            this.callDriver();
        });

        // Rating system
        document.querySelectorAll('.star').forEach(star => {
            star.addEventListener('click', (e) => {
                this.setRating(parseInt(e.target.dataset.rating));
            });
        });

        document.getElementById('submitRating')?.addEventListener('click', () => {
            this.submitTripRating();
        });

        // Add favorite location
        document.getElementById('addFavoriteBtn')?.addEventListener('click', () => {
            this.addFavoriteLocation();
        });
    }

    async checkAuthentication() {
        try {
            this.authToken = this.getAuthToken();

            if (!this.authToken) {
                console.log('No auth token found');
                return false;
            }

            // Verify token with backend
            const response = await fetch('/api/v1/users/profile/', {
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
                this.currentUser = await response.json();
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

        // Check if user account is active
        if (this.currentUser && this.currentUser.status !== 'active') {
            this.showNotification('Your account is not active. Please contact support.', 'error');
            return false;
        }

        // User permissions - all authenticated users can perform basic actions
        const userActions = [
            'book_trip', 'cancel_trip', 'view_trips', 'rate_trip',
            'manage_favorites', 'topup_wallet', 'view_profile'
        ];

        if (userActions.includes(action)) {
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
        this.currentUser = null;
        this.isAuthenticated = false;
    }

    async loadUserData() {
        if (!this.checkPermission('view_profile')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/profile/');

            if (response && response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                document.getElementById('userName').textContent = userData.first_name;
                document.getElementById('walletBalance').textContent = userData.wallet_balance.toFixed(2);
                document.getElementById('walletBalanceDetailed').textContent = userData.wallet_balance.toFixed(2);
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    async loadRecentTrips() {
        if (!this.checkPermission('view_trips')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/trips/?limit=5');

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
                    <small class="text-muted">$${trip.total_amount}</small>
                    <span class="badge bg-${this.getStatusColor(trip.status)}">${trip.status}</span>
                </div>
            `;
            container.appendChild(tripElement);
        });
    }

    async loadUserStats() {
        if (!this.checkPermission('view_profile')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/stats/');

            if (response && response.ok) {
                const stats = await response.json();
                document.querySelector('[data-stat="total-trips"]').textContent = stats.total_trips;
                document.querySelector('[data-stat="total-spent"]').textContent = `$${stats.total_spent}`;
                document.querySelector('[data-stat="avg-rating"]').textContent = stats.avg_rating.toFixed(1);
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }

    async loadFavoriteLocations() {
        if (!this.checkPermission('manage_favorites')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/favorites/');

            if (response && response.ok) {
                const favorites = await response.json();
                this.displayFavoriteLocations(favorites);
            }
        } catch (error) {
            console.error('Error loading favorite locations:', error);
        }
    }

    displayFavoriteLocations(favorites) {
        const container = document.getElementById('favoriteLocations');
        container.innerHTML = '';

        favorites.forEach(favorite => {
            const favoriteElement = document.createElement('div');
            favoriteElement.className = 'mb-2 p-2 border rounded cursor-pointer';
            favoriteElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-star text-warning me-2"></i>
                        <strong>${favorite.name}</strong>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="this.removeFavorite(${favorite.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <small class="text-muted ms-3">${favorite.address}</small>
            `;

            favoriteElement.addEventListener('click', () => {
                this.setPickupLocation(favorite.latitude, favorite.longitude);
            });

            container.appendChild(favoriteElement);
        });
    }

    async bookRide() {
        if (!this.checkPermission('book_trip')) return;

        const bookBtn = document.getElementById('bookRideBtn');
        const originalText = bookBtn.innerHTML;

        bookBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Booking...';
        bookBtn.disabled = true;

        try {
            const tripData = {
                pickup_latitude: parseFloat(document.getElementById('pickupLat').value),
                pickup_longitude: parseFloat(document.getElementById('pickupLng').value),
                pickup_address: document.getElementById('pickupLocation').value,
                dropoff_latitude: parseFloat(document.getElementById('dropoffLat').value),
                dropoff_longitude: parseFloat(document.getElementById('dropoffLng').value),
                dropoff_address: document.getElementById('dropoffLocation').value,
                trip_type: document.getElementById('tripType').value,
                scheduled_at: document.getElementById('scheduleTime').value || null,
                discount_code: document.getElementById('discountCode').value || null
            };

            const response = await this.makeAuthenticatedRequest('/api/v1/users/trips/', {
                method: 'POST',
                body: JSON.stringify(tripData)
            });

            if (response && response.ok) {
                const trip = await response.json();
                this.currentTrip = trip;
                this.showTripStatus();
                this.startTripPolling();
                this.showNotification('Trip booked successfully! Looking for a driver...', 'success');
            } else if (response) {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to book trip', 'error');
            }
        } catch (error) {
            console.error('Error booking trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            bookBtn.innerHTML = originalText;
            bookBtn.disabled = false;
        }
    }

    showTripStatus() {
        document.getElementById('bookingForm').style.display = 'none';
        document.getElementById('tripStatus').style.display = 'block';
        this.updateTripStatus();
    }

    updateTripStatus() {
        if (!this.currentTrip) return;

        const statusText = document.getElementById('statusText');
        const driverInfo = document.getElementById('driverInfo');
        const cancelBtn = document.getElementById('cancelTripBtn');
        const callBtn = document.getElementById('callDriverBtn');

        switch (this.currentTrip.status) {
            case 'pending':
                statusText.innerHTML = '<span class="text-warning">Looking for a driver...</span>';
                driverInfo.style.display = 'none';
                cancelBtn.style.display = 'block';
                callBtn.style.display = 'none';
                break;

            case 'accepted':
                statusText.innerHTML = '<span class="text-info">Driver found! Driver is on the way...</span>';
                this.showDriverInfo();
                cancelBtn.style.display = 'block';
                callBtn.style.display = 'block';
                break;

            case 'in_progress':
                statusText.innerHTML = '<span class="text-success">Trip in progress</span>';
                this.showDriverInfo();
                cancelBtn.style.display = 'none';
                callBtn.style.display = 'block';
                break;

            case 'completed':
                this.showTripCompletion();
                break;

            case 'cancelled':
                this.showTripCancellation();
                break;
        }
    }

    showDriverInfo() {
        const driverInfo = document.getElementById('driverInfo');
        driverInfo.style.display = 'block';

        if (this.currentTrip.driver) {
            document.getElementById('driverName').textContent = this.currentTrip.driver.first_name;
            document.getElementById('driverPhone').textContent = this.currentTrip.driver.phone;
            document.getElementById('driverRating').textContent = this.currentTrip.driver.rating || '5.0';
            document.getElementById('vehicleInfo').textContent =
                `${this.currentTrip.driver.vehicle_make} ${this.currentTrip.driver.vehicle_model}`;
            document.getElementById('licensePlate').textContent = this.currentTrip.driver.license_plate;
        }
    }

    async checkActiveTrip() {
        if (!this.checkPermission('view_trips')) return;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/trips/active/');

            if (response && response.ok) {
                const trip = await response.json();
                if (trip) {
                    this.currentTrip = trip;
                    this.showTripStatus();
                    this.startTripPolling();
                }
            }
        } catch (error) {
            console.error('Error checking active trip:', error);
        }
    }

    startTripPolling() {
        if (!this.checkPermission('view_trips')) return;

        if (this.tripPolling) {
            clearInterval(this.tripPolling);
        }

        this.tripPolling = setInterval(async () => {
            try {
                const response = await this.makeAuthenticatedRequest(`/api/v1/users/trips/${this.currentTrip.id}/`);

                if (response && response.ok) {
                    const updatedTrip = await response.json();
                    this.currentTrip = updatedTrip;
                    this.updateTripStatus();

                    if (['completed', 'cancelled'].includes(updatedTrip.status)) {
                        clearInterval(this.tripPolling);
                        this.tripPolling = null;
                    }
                }
            } catch (error) {
                console.error('Error polling trip status:', error);
            }
        }, 5000); // Poll every 5 seconds
    }

    async cancelTrip() {
        if (!this.checkPermission('cancel_trip')) return;

        if (!confirm('Are you sure you want to cancel this trip?')) {
            return;
        }

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/users/trips/${this.currentTrip.id}/cancel/`, {
                method: 'POST'
            });

            if (response && response.ok) {
                this.showNotification('Trip cancelled successfully', 'success');
                this.resetBookingForm();
            } else {
                this.showNotification('Failed to cancel trip', 'error');
            }
        } catch (error) {
            console.error('Error cancelling trip:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    callDriver() {
        if (this.currentTrip && this.currentTrip.driver) {
            window.open(`tel:${this.currentTrip.driver.phone}`);
        }
    }

    showTripCompletion() {
        clearInterval(this.tripPolling);
        this.showNotification('Trip completed successfully!', 'success');

        // Show rating modal
        const ratingModal = new bootstrap.Modal(document.getElementById('ratingModal'));
        ratingModal.show();

        this.resetBookingForm();
    }

    showTripCancellation() {
        clearInterval(this.tripPolling);
        this.showNotification('Trip was cancelled', 'warning');
        this.resetBookingForm();
    }

    resetBookingForm() {
        document.getElementById('bookingForm').style.display = 'block';
        document.getElementById('tripStatus').style.display = 'none';
        document.getElementById('bookingForm').reset();

        // Clear map markers
        if (this.pickupMarker) {
            this.map.removeLayer(this.pickupMarker);
            this.pickupMarker = null;
        }
        if (this.dropoffMarker) {
            this.map.removeLayer(this.dropoffMarker);
            this.dropoffMarker = null;
        }
        if (this.routeControl) {
            this.map.removeControl(this.routeControl);
            this.routeControl = null;
        }

        document.getElementById('estimatedFare').textContent = '$0.00';
        this.currentTrip = null;
    }

    async applyDiscountCode() {
        if (!this.checkPermission('book_trip')) return;

        const code = document.getElementById('discountCode').value;
        if (!code) return;

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/discounts/validate/${code}/`);

            if (response && response.ok) {
                const discount = await response.json();
                const discountInfo = document.getElementById('discountInfo');
                discountInfo.style.display = 'block';
                discountInfo.textContent = `${discount.discount_percentage}% discount applied!`;
                discountInfo.className = 'text-success';

                this.showNotification('Discount code applied successfully!', 'success');
            } else if (response) {
                const error = await response.json();
                this.showNotification(error.detail || 'Invalid discount code', 'error');
            }
        } catch (error) {
            console.error('Error applying discount:', error);
            this.showNotification('Error validating discount code', 'error');
        }
    }

    async topupWallet() {
        if (!this.checkPermission('topup_wallet')) return;

        const amount = parseFloat(document.getElementById('topupAmount').value);
        const paymentMethod = document.getElementById('paymentMethod').value;

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/wallet/topup/', {
                method: 'POST',
                body: JSON.stringify({
                    amount: amount,
                    payment_method: paymentMethod
                })
            });

            if (response && response.ok) {
                const result = await response.json();
                this.showNotification(`$${amount} added to wallet successfully!`, 'success');

                // Update wallet balance displays
                document.getElementById('walletBalance').textContent = result.new_balance.toFixed(2);
                document.getElementById('walletBalanceDetailed').textContent = result.new_balance.toFixed(2);

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('topupModal'));
                modal.hide();

                // Reset form
                document.getElementById('topupForm').reset();
            } else if (response) {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to add money to wallet', 'error');
            }
        } catch (error) {
            console.error('Error topping up wallet:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    setRating(rating) {
        this.selectedRating = rating;
        const stars = document.querySelectorAll('.star');
        const ratingText = document.getElementById('ratingText');

        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('text-warning');
                star.classList.remove('text-muted');
            } else {
                star.classList.add('text-muted');
                star.classList.remove('text-warning');
            }
        });

        const ratingTexts = ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];
        ratingText.textContent = ratingTexts[rating];
    }

    async submitTripRating() {
        if (!this.checkPermission('rate_trip')) return;

        if (this.selectedRating === 0) {
            this.showNotification('Please select a rating', 'warning');
            return;
        }

        const comment = document.getElementById('tripComment').value;

        try {
            const response = await this.makeAuthenticatedRequest(`/api/v1/users/trips/${this.currentTrip.id}/rate/`, {
                method: 'POST',
                body: JSON.stringify({
                    rating: this.selectedRating,
                    comment: comment
                })
            });

            if (response && response.ok) {
                this.showNotification('Thank you for your rating!', 'success');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('ratingModal'));
                modal.hide();

                // Reset rating
                this.selectedRating = 0;
                document.getElementById('tripComment').value = '';
                this.setRating(0);

                // Reload recent trips
                this.loadRecentTrips();
            } else {
                this.showNotification('Failed to submit rating', 'error');
            }
        } catch (error) {
            console.error('Error submitting rating:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async addFavoriteLocation() {
        if (!this.checkPermission('manage_favorites')) return;

        const name = prompt('Enter a name for this location:');
        if (!name) return;

        const address = prompt('Enter the address:');
        if (!address) return;

        // For simplicity, use user's current location or map center
        const center = this.map.getCenter();

        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/users/favorites/', {
                method: 'POST',
                body: JSON.stringify({
                    name: name,
                    address: address,
                    latitude: center.lat,
                    longitude: center.lng
                })
            });

            if (response && response.ok) {
                this.showNotification('Favorite location added!', 'success');
                this.loadFavoriteLocations();
            } else {
                this.showNotification('Failed to add favorite location', 'error');
            }
        } catch (error) {
            console.error('Error adding favorite location:', error);
            this.showNotification('Network error. Please try again.', 'error');
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
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UserDashboard();
});
