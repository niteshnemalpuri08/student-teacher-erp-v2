// frontend/student_dash/student_sync.js

const STUDENT_SYNC = {
    // 1. Get Current Logged-in Student
    getCurrentStudent: function() {
        const stored = localStorage.getItem('user');
        // Default to 24cse001 if testing without login
        return stored ? JSON.parse(stored).username : '24cse001'; 
    },

    // 2. Fetch Real Data from Shared Database
    getData: function() {
        const studentID = this.getCurrentStudent(); // "24cse001"
        
        // Access the Shared DB (DATA_STORE must be loaded in HTML)
        if (typeof DATA_STORE === 'undefined') {
            console.error("DATA_STORE not loaded! Make sure data_store.js is included.");
            return null;
        }

        const data = DATA_STORE.getStudent(studentID);
        
        if (!data) return null;

        return {
            roll: studentID,
            name: data.name,
            stats: {
                attendance: data.attendance_percent,
                avgScore: data.avg_score,
                assignmentsPending: data.assignments_pending,
                behaviorScore: Math.min(100, data.attendance_percent + 10)
            },
            // Map Exact Marks
            marks: [
                { name: 'Mathematics', val: data.subjects_marks['Mathematics'] },
                { name: 'Physics', val: data.subjects_marks['Physics'] },
                { name: 'Chemistry', val: data.subjects_marks['Chemistry'] },
                { name: 'Computer Science', val: data.subjects_marks['Computer Science'] },
                { name: 'English', val: data.subjects_marks['English'] },
                { name: 'Physical Education', val: data.subjects_marks['Physical Education'] }
            ],
            // Map Exact Attendance
            attendance: [
                { name: 'Mathematics', pct: data.subjects_attendance['Mathematics'] },
                { name: 'Physics', pct: data.subjects_attendance['Physics'] },
                { name: 'Chemistry', pct: data.subjects_attendance['Chemistry'] },
                { name: 'Computer Science', pct: data.subjects_attendance['Computer Science'] },
                { name: 'English', pct: data.subjects_attendance['English'] },
                { name: 'Physical Education', pct: data.subjects_attendance['Physical Education'] }
            ]
        };
    }
};