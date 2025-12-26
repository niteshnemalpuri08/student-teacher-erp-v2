// Authentication utilities for JWT token management

const authManager = {
    // Decode base64url encoded JWT payload
    decodeBase64Url: function(base64Url) {
        // Convert base64url to base64
        let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        // Add padding if needed
        while (base64.length % 4 !== 0) {
            base64 += '=';
        }
        // Decode and parse JSON
        try {
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error('Error decoding JWT payload:', e);
            return null;
        }
    },

    // Check if JWT token is expired
    isTokenExpired: function(token) {
        if (!token) return true;

        try {
            const parts = token.split('.');
            if (parts.length !== 3) return true;

            const payload = this.decodeBase64Url(parts[1]);
            if (!payload || !payload.exp) return true;

            const currentTime = Math.floor(Date.now() / 1000);
            return payload.exp < currentTime;
        } catch (e) {
            console.error('Error checking token expiration:', e);
            return true;
        }
    },

    // Get user data from localStorage
    getUser: function() {
        try {
            const userData = localStorage.getItem('user');
            return userData ? JSON.parse(userData) : null;
        } catch (e) {
            console.error('Error getting user data:', e);
            return null;
        }
    },

    // Store user data in localStorage
    setUser: function(userData) {
        try {
            localStorage.setItem('user', JSON.stringify(userData));
        } catch (e) {
            console.error('Error storing user data:', e);
        }
    },

    // Clear user data and redirect to login
    logout: function() {
        localStorage.removeItem('user');
        window.location.href = '../login.html';
    },

    // Make authenticated API call
    apiCall: async function(url, options = {}) {
        const user = this.getUser();
        if (!user || !user.token) {
            throw new Error('No authentication token available');
        }

        if (this.isTokenExpired(user.token)) {
            this.logout();
            throw new Error('Token expired');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${user.token}`,
                'Content-Type': 'application/json'
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };
        if (options.headers) {
            mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
        }

        const response = await fetch(url, mergedOptions);

        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication failed');
        }

        return response;
    }
};

// Make authManager globally available
window.authManager = authManager;
