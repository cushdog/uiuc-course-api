import sqlite3
from test import perform_search

# Database connection (update the path to your database file)
DATABASE_URL = '../../data/DB/master.db'

def update_average_gpa():
    # Connect to the database
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Fetch all rows from the courses table
    cursor.execute("SELECT * FROM courses")
    rows = cursor.fetchall()

    for row in rows:
        # Unpack the fields needed for course_search_term
        subject = row[2]  # Assuming 'subject' is at index 2
        course_number = row[3]  # Assuming 'course_number' is at index 3
        
        # Create the course_search_term
        course_search_term = f"{subject} {course_number}"
        
        # Call perform_search with the course_search_term and an empty list for filters
        new_average_gpa = perform_search(course_search_term, [])

        # Update the average_gpa in the table
        cursor.execute("""
            UPDATE courses
            SET average_gpa = ?
            WHERE subject = ? AND course_number = ?
        """, (new_average_gpa, subject, course_number))
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_average_gpa()
