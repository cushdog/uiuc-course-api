import sqlite3
from test import perform_search
import os

# Database connections
MASTER_DB_URL = '../../data/DB/master.db'
PROFESSOR_STATS_DB_URL = '../../data/DB/professor_stats.db'

def create_professor_stats_db():
    conn = sqlite3.connect(PROFESSOR_STATS_DB_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS professor_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class TEXT,
        professor TEXT,
        avg_gpa REAL,
        total_students INTEGER,
        UNIQUE(class, professor)
    )
    ''')
    
    conn.commit()
    conn.close()

def update_professor_stats():
    # Create the new database if it doesn't exist
    if not os.path.exists(PROFESSOR_STATS_DB_URL):
        create_professor_stats_db()
    
    # Connect to both databases
    master_conn = sqlite3.connect(MASTER_DB_URL)
    master_cursor = master_conn.cursor()
    
    prof_conn = sqlite3.connect(PROFESSOR_STATS_DB_URL)
    prof_cursor = prof_conn.cursor()
    
    # Fetch all unique classes from the courses table in the master database
    master_cursor.execute("SELECT DISTINCT subject, course_number FROM courses")
    classes = master_cursor.fetchall()
    
    for subject, course_number in classes:
        course_search_term = f"{subject} {course_number}"
        
        # Call perform_search with the course_search_term and an empty list for filters
        prof_stats = perform_search(course_search_term, [])
        
        if prof_stats:
            # Insert or update professor stats for this class in the new database
            for prof in prof_stats:
                prof_cursor.execute('''
                INSERT OR REPLACE INTO professor_stats (class, professor, avg_gpa, total_students)
                VALUES (?, ?, ?, ?)
                ''', (course_search_term, prof['prof'], float(prof['avg']), prof['total']))
    
    prof_conn.commit()
    master_conn.close()
    prof_conn.close()

def print_professor_stats(class_name):
    conn = sqlite3.connect(PROFESSOR_STATS_DB_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT professor, avg_gpa, total_students
    FROM professor_stats
    WHERE class = ?
    ORDER BY avg_gpa DESC
    ''', (class_name,))
    
    results = cursor.fetchall()
    
    if results:
        print(f"Professor stats for {class_name}:")
        for prof, avg_gpa, total_students in results:
            print(f"  - {prof} | Total Students: {total_students} | Avg GPA: {avg_gpa:.3f}")
    else:
        print(f"No data found for {class_name}")
    
    conn.close()

if __name__ == "__main__":
    update_professor_stats()
    
    # Example usage
    print_professor_stats("MATH 424")