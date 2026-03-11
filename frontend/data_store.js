// data_store.js - The Shared "Database"
// UPDATED: Version 6.0 - Stores Exact Subject Attendance

const DATA_STORE = {
    // Increment to force data reset
    DB_VERSION: '6.0', 

    init: function() {
        const storedVersion = localStorage.getItem('db_version');
        
        if (!localStorage.getItem('student_attendance_db') || storedVersion !== this.DB_VERSION) {
            console.log("Initializing Database: Version 6.0 (Subject Attendance Sync)...");
            const db = {};
            
            for (let i = 1; i <= 200; i++) {
                const idSuffix = String(i).padStart(3, '0');
                const roll = `24cse${idSuffix}`;
                
                let subjects_marks = {};
                let subjects_attendance = {};
                let total_present_avg = 0;

                // -------------------------------------------------------------
                // 1. SPECIFIC DATA FOR STUDENT 1 (24cse001)
                // -------------------------------------------------------------
                if (i === 1) {
                    // Exact Attendance Data you want Parent & Student to see
                    subjects_attendance = {
                        'Mathematics': 96,
                        'Physics': 85,
                        'Chemistry': 90,
                        'Computer Science': 98,
                        'English': 92,
                        'Physical Education': 100
                    };
                    
                    subjects_marks = {
                        'Mathematics': 95, 'Physics': 88, 'Chemistry': 92,
                        'Computer Science': 98, 'English': 85, 'Physical Education': 96
                    };
                } 
                // -------------------------------------------------------------
                // 2. DATA FOR STUDENTS 2-200 (Deterministic)
                // -------------------------------------------------------------
                else {
                    const seed = (i * 9301 + 49297) % 233280;
                    
                    // Generate marks and attendance deterministically
                    subjects_marks = {
                        'Mathematics': 40 + ((i * 3 + 7) % 61),
                        'Physics': 40 + ((i * 5 + 11) % 61),
                        'Chemistry': 40 + ((i * 7 + 2) % 61),
                        'Computer Science': 40 + ((i * 2 + 19) % 61),
                        'English': 50 + ((i * 4 + 1) % 51),
                        'Physical Education': 60 + ((i * 8 + 3) % 41)
                    };

                    // Attendance is usually slightly higher than marks in this logic
                    subjects_attendance = {
                        'Mathematics': Math.min(100, subjects_marks['Mathematics'] + 5),
                        'Physics': Math.min(100, subjects_marks['Physics'] + 2),
                        'Chemistry': Math.min(100, subjects_marks['Chemistry'] + 4),
                        'Computer Science': Math.min(100, subjects_marks['Computer Science'] + 8),
                        'English': Math.min(100, subjects_marks['English'] + 10),
                        'Physical Education': 95
                    };
                }

                // Calculate Overall Attendance Percentage from the subject averages
                const attValues = Object.values(subjects_attendance);
                total_present_avg = Math.round(attValues.reduce((a, b) => a + b, 0) / 6);

                // Calculate Overall Marks Average
                const scoreValues = Object.values(subjects_marks);
                const avgScore = Math.round(scoreValues.reduce((a, b) => a + b, 0) / 6);

                db[roll] = {
                    name: `Student ${i}`,
                    total_classes: 100, // Normalized base
                    classes_present: total_present_avg,
                    attendance_percent: total_present_avg, // Overall %
                    
                    // STORE BOTH OBJECTS
                    subjects_marks: subjects_marks, 
                    subjects_attendance: subjects_attendance, // <--- NEW: Exact attendance per subject
                    
                    avg_score: avgScore,
                    assignments_pending: (i % 5)
                };
            }
            
            localStorage.setItem('student_attendance_db', JSON.stringify(db));
            localStorage.setItem('db_version', this.DB_VERSION);
            console.log("Database Ready with Subject Attendance.");
        }
    },

    getStudent: function(roll) {
        this.init(); 
        const db = JSON.parse(localStorage.getItem('student_attendance_db'));
        return db[roll.toLowerCase()] || null;
    },

    // (Teacher update logic would go here, updating the specific subject attendance)
    // For now, we keep the simple markAttendance update for overall
    markAttendance: function(roll, isPresent) {
        this.init();
        const db = JSON.parse(localStorage.getItem('student_attendance_db'));
        const key = roll.toLowerCase();
        if (db[key]) {
            db[key].total_classes += 1;
            if (isPresent) db[key].classes_present += 1;
            db[key].attendance_percent = Math.round((db[key].classes_present / db[key].total_classes) * 100);
        }
        localStorage.setItem('student_attendance_db', JSON.stringify(db));
    },

    getRange: function(start, end) {
        this.init();
        const db = JSON.parse(localStorage.getItem('student_attendance_db'));
        const students = [];
        for (let i = start; i <= end; i++) {
            const idSuffix = String(i).padStart(3, '0');
            const roll = `24cse${idSuffix}`;
            if(db[roll]) students.push({ roll: roll, ...db[roll] });
        }
        return students;
    }
};