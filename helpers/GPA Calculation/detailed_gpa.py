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
    CREATE TABLE IF NOT EXISTS class_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class TEXT UNIQUE,
        avg_gpa REAL
    )
    ''')
    
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
        result = perform_search(course_search_term, [])
        
        if result is not None:
            class_avg_gpa, prof_stats = result
            
            # Insert or update class-wide stats if available
            if class_avg_gpa is not None:
                prof_cursor.execute('''
                INSERT OR REPLACE INTO class_stats (class, avg_gpa)
                VALUES (?, ?)
                ''', (course_search_term, class_avg_gpa))
            
            # Insert or update professor stats for this class if available
            if prof_stats:
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
    
    # Fetch class-wide average GPA
    cursor.execute('SELECT avg_gpa FROM class_stats WHERE class = ?', (class_name,))
    class_avg = cursor.fetchone()
    
    if class_avg and class_avg[0] is not None:
        print(f"Class stats for {class_name}:")
        print(f"  Class-wide Avg GPA: {class_avg[0]:.3f}")
    else:
        print(f"No class-wide average GPA available for {class_name}")
    
    # Fetch professor stats
    cursor.execute('''
    SELECT professor, avg_gpa, total_students
    FROM professor_stats
    WHERE class = ?
    ORDER BY avg_gpa DESC
    ''', (class_name,))
    
    results = cursor.fetchall()
    
    if results:
        print("Professor stats:")
        for prof, avg_gpa, total_students in results:
            if avg_gpa is not None and total_students is not None:
                print(f"  - {prof} | Total Students: {total_students} | Avg GPA: {avg_gpa:.3f}")
            else:
                print(f"  - {prof} | Data not available")
    else:
        print(f"No professor data found for {class_name}")
    
    conn.close()

if __name__ == "__main__":
    update_professor_stats()
    
    # Example usage
    print_professor_stats("MATH 424")