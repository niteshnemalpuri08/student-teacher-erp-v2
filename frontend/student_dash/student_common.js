/**
 * student_common.js
 * Single Source of Truth for Student Data
 */

const STUDENT_COMMON = {
    // CENTRAL MOCK DATA - Used if backend fails
    // This ensures that even in demo mode, all pages show the same numbers.
    MOCK_DATA: {
        user: {
            username: 'student_demo',
            roll: '24cse001',
            name: 'Demo Student',
            class: '12th Grade'
        },
        // These subjects determine the 94% attendance and 89% avg score
        subjects: [
            { name: 'Mathematics', total: 40, present: 38, score: 92, assignments: 90, exams: 92, trend: 'up' },
            { name: 'Physics',     total: 40, present: 36, score: 87, assignments: 85, exams: 87, trend: 'up' },
            { name: 'Chemistry',   total: 40, present: 37, score: 89, assignments: 88, exams: 89, trend: 'stable' },
            { name: 'Comp Sci',    total: 40, present: 39, score: 95, assignments: 95, exams: 95, trend: 'up' },
            { name: 'English',     total: 40, present: 35, score: 82, assignments: 80, exams: 82, trend: 'stable' },
            { name: 'Physical Ed', total: 20, present: 20, score: 91, assignments: 90, exams: 91, trend: 'up' }
        ],
        notifications: 4,
        upcoming_events: 2
    },

    /**
     * Main function to fetch all data.
     * Tries Backend API first -> Falls back to MOCK_DATA.
     */
    getAllData: async function() {
        // 1. Try to get User
        let user = authManager.getUser();
        if (!user) return this.MOCK_DATA;

        let serverData = null;

        try {
            // 2. Try to fetch fresh data from Backend
            // We assume an endpoint that returns { user:..., subjects: [...] }
            const response = await authManager.apiCall(`/api/student/dashboard-summary?username=${user.username}`);
            if (response.ok) {
                serverData = await response.json();
            }
        } catch (e) {
            console.warn("Backend unavailable, using consistent mock data.");
        }

        // 3. Merge Server Data or use Mock
        const rawSubjects = (serverData && serverData.subjects) ? serverData.subjects : this.MOCK_DATA.subjects;
        const profile = (serverData && serverData.user) ? serverData.user : (user || this.MOCK_DATA.user);

        // 4. Calculate Aggregates (Math happens HERE only)
        const stats = this.calculateStats(rawSubjects);

        return {
            user: profile,
            subjects: rawSubjects,
            stats: stats,
            notifications: (serverData && serverData.notifications) || this.MOCK_DATA.notifications,
            upcoming: (serverData && serverData.upcoming_events) || this.MOCK_DATA.upcoming_events
        };
    },

    /**
     * consistent Math Calculator
     */
    calculateStats: function(subjects) {
        let totalClasses = 0;
        let totalPresent = 0;
        let totalScore = 0;
        let scoreCount = 0;
        let improving = 0;

        subjects.forEach(sub => {
            // Attendance
            totalClasses += sub.total || 0;
            totalPresent += sub.present || 0;
            
            // Grades (exclude Physical Ed from academic average if desired, currently including all)
            if (sub.score !== undefined) {
                totalScore += sub.score;
                scoreCount++;
            }

            if (sub.trend === 'up') improving++;
        });

        // Avoid division by zero
        const overallAttendance = totalClasses > 0 ? Math.round((totalPresent / totalClasses) * 100) : 0;
        const avgScore = scoreCount > 0 ? Math.round((totalScore / scoreCount) * 10) / 10 : 0; // 1 decimal

        return {
            totalClasses,
            totalPresent,
            totalAbsent: totalClasses - totalPresent,
            overallAttendance, // e.g. 94
            avgScore,          // e.g. 89.3
            avgGrade: this.getGrade(avgScore),
            improvingCount: improving
        };
    },

    getGrade: function(score) {
        if (score >= 90) return 'A';
        if (score >= 85) return 'A-';
        if (score >= 80) return 'B+';
        if (score >= 75) return 'B';
        if (score >= 70) return 'C+';
        if (score >= 60) return 'C';
        return 'D';
    },

    getGradeClass: function(score) {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'good';
        if (score >= 70) return 'average';
        return 'poor';
    }
};

// Expose globally
window.STUDENT_COMMON = STUDENT_COMMON;