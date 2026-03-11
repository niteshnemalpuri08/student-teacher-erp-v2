// frontend/auth.js

const authManager = {
    // 1. Get User Data
    getUser: function() {
        // 🔥 FIXED: Changed 'user' to 'schoolUser' to match login page
        const userStr = localStorage.getItem('schoolUser');
        if (!userStr) return null;
        try {
            return JSON.parse(userStr);
        } catch (e) {
            return null;
        }
    },

    // 2. Check Auth on Page Load
    checkAuth: function() {
        const user = this.getUser();
        if (!user) {
            // Not logged in -> Go to Login
            if (window.location.pathname.includes('_dash')) {
                window.location.href = '../login.html';
            } else {
                window.location.href = 'login.html';
            }
            return false;
        }
        return true;
    },

    // 3. Login Helper
    login: function(userData) {
        // 🔥 FIXED: Saving consistent key
        localStorage.setItem('schoolUser', JSON.stringify(userData));
    },

    // 4. Logout
    logout: function() {
        localStorage.removeItem('schoolUser');
        window.location.href = '../login.html';
    }
};

// Auto-run check
if (!window.location.pathname.endsWith('login.html')) {
    // authManager.checkAuth(); 
}

// Export to window
window.authManager = authManager;