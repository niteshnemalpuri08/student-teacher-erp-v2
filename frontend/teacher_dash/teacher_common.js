// teacher_common.js - Connects to Shared Data Store

const TEACHER_COMMON = {
    TEACHER_MAP: {
        't01': { section: 'Section A', start: 1, end: 40 },
        't02': { section: 'Section B', start: 41, end: 80 },
        't03': { section: 'Section C', start: 81, end: 120 },
        't04': { section: 'Section D', start: 121, end: 160 },
        't05': { section: 'Section E', start: 161, end: 200 }
    },

    getCurrentTeacher: function() {
        const stored = localStorage.getItem('user');
        return stored ? JSON.parse(stored).username : 't01';
    },

    checkAuth: function() {
        const user = JSON.parse(localStorage.getItem('user'));
        if (!user || user.role !== 'teacher') {
            window.location.href = '../login.html';
            return false;
        }
        return true;
    },

    // FETCH REAL DATA FROM DATA_STORE
    getAccessibleStudents: async function() {
        const teacherId = this.getCurrentTeacher();
        const config = this.TEACHER_MAP[teacherId] || this.TEACHER_MAP['t01'];
        
        // Use the shared data store
        const rawData = DATA_STORE.getRange(config.start, config.end);

        const students = rawData.map(s => {
            // Determine Status based on REAL percentage
            let status = 'Good';
            if (s.stats.attendance_percent < 60) status = 'Critical';
            else if (s.stats.attendance_percent < 75) status = 'Average';

            return {
                roll: s.roll,
                name: s.name,
                attendance: s.stats.attendance_percent, // The Real Number
                total_classes: s.stats.total_classes,
                present: s.stats.classes_present,
                avg_marks: 75, // Static for now, or add to data_store if needed
                section: config.section,
                status: status
            };
        });

        return {
            section: config.section,
            range: `${config.start}-${config.end}`,
            students: students
        };
    },

    calculateStats: function(students) {
        const total = students.length;
        const low = students.filter(s => s.attendance < 75 && s.attendance >= 60).length;
        const critical = students.filter(s => s.attendance < 60).length;
        const sum = students.reduce((acc, curr) => acc + curr.attendance, 0);
        const avg = total > 0 ? Math.round(sum / total) : 0;

        return {
            totalStudents: total,
            avgAttendance: avg,
            lowAttendance: low,
            criticalRisk: critical,
            good: total - low - critical
        };
    }
};