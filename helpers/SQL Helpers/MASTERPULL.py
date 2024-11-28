import requests
import xml.etree.ElementTree as ET
import sqlite3
import time

# Helper Functions
def fetch_xml(url):
    """Fetch XML content from a URL and parse it."""
    print(f"Fetching URL: {url}")
    response = requests.get(url)
    time.sleep(1)  # Added 1-second delay between API calls
    return ET.fromstring(response.content)

def safe_find(root, element):
    """Safely find an element in XML and return its text."""
    found = root.find(element)
    if found is not None:
        return found.text
    else:
        print(f"  Warning: Element '{element}' not found.")
        return None

# Data Extraction Functions
def extract_main_info(root):
    """Extract main course information."""
    print("Extracting main course information...")
    info = {
        'label': safe_find(root, 'label'),
        'description': safe_find(root, 'description'),
        'creditHours': safe_find(root, 'creditHours')
    }
    print(f"  Course Label: {info['label']}")
    print(f"  Credit Hours: {info['creditHours']}")
    return info

def extract_section_info(root):
    """Extract section information, including all instructors."""
    print("Extracting section information...")
    info = {
        'sectionNumber': safe_find(root, 'sectionNumber'),
        'sectionTitle': safe_find(root, 'sectionTitle'),
        'statusCode': safe_find(root, 'statusCode'),
        'sectionText': safe_find(root, 'sectionText'),
        'sectionNotes': safe_find(root, 'sectionNotes'),
        'sectionCappArea': safe_find(root, 'sectionCappArea'),
        'enrollmentStatus': safe_find(root, 'enrollmentStatus'),
        'startDate': safe_find(root, 'startDate'),
        'endDate': safe_find(root, 'endDate'),
        'meetingType': None,
        'meetingStart': None,
        'meetingEnd': None,
        'meetingDays': None,
        'meetingRoom': None,
        'meetingBuilding': None,
        'instructor': None
    }

    # Collect all instructors from all meetings
    instructors_set = set()
    meetings = root.find('meetings')
    if meetings is not None:
        print("  Extracting meeting information...")
        for meeting in meetings:
            # Extract meeting details if needed
            info['meetingType'] = safe_find(meeting, 'type')
            info['meetingStart'] = safe_find(meeting, 'start')
            info['meetingEnd'] = safe_find(meeting, 'end')
            info['meetingDays'] = safe_find(meeting, 'daysOfTheWeek')
            info['meetingRoom'] = safe_find(meeting, 'roomNumber')
            info['meetingBuilding'] = safe_find(meeting, 'buildingName')

            # Extract instructors
            instructors = meeting.find('instructors')
            if instructors is not None:
                print("    Extracting instructors...")
                for instructor in instructors:
                    if instructor.text:
                        instructors_set.add(instructor.text)
                        print(f"      Found instructor: {instructor.text}")

    else:
        print("  No meetings found.")

    info['instructor'] = list(instructors_set) if instructors_set else None
    print(f"  Instructors: {info['instructor']}")
    return info

# Database Functions
def create_table(conn):
    """Create the courses table if it doesn't exist."""
    print("Creating 'courses' table if it doesn't exist...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            year INTEGER,
            semester TEXT,
            subject TEXT,
            course_number TEXT,
            label TEXT,
            description TEXT,
            creditHours TEXT,
            sectionNumber TEXT,
            statusCode TEXT,
            sectionText TEXT,
            sectionNotes TEXT,
            sectionCappArea TEXT,
            enrollmentStatus TEXT,
            startDate TEXT,
            endDate TEXT,
            meetingType TEXT,
            meetingStart TEXT,
            meetingEnd TEXT,
            meetingDays TEXT,
            meetingRoom TEXT,
            meetingBuilding TEXT,
            instructor TEXT,
            field23 TEXT,
            field24 TEXT,
            field25 TEXT,
            sectionTitle TEXT,
            crn TEXT,
            department TEXT  -- Added this line
        )
    ''')
    print("  'courses' table is ready.")

def add_department_column(conn):
    """Add the 'department' column to the 'courses' table if it doesn't exist."""
    print("Checking if 'department' column exists in 'courses' table...")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(courses)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'department' not in columns:
        print("  'department' column not found. Adding column...")
        conn.execute('ALTER TABLE courses ADD COLUMN department TEXT')
        print("  'department' column added.")
    else:
        print("  'department' column already exists.")

def insert_course(conn, year, semester, subject, course_number, main_info, section_info, crn, unitName):
    """Insert a new course record into the database."""
    print(f"Inserting course {subject} {course_number} into database...")
    instructor_str = ', '.join(section_info['instructor']) if section_info['instructor'] else None
    conn.execute('''
        INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        year, semester, subject, course_number,
        main_info['label'], main_info['description'], main_info['creditHours'],
        section_info['sectionNumber'], section_info['statusCode'], section_info['sectionText'],
        section_info['sectionNotes'], section_info['sectionCappArea'], section_info['enrollmentStatus'],
        section_info['startDate'], section_info['endDate'], section_info['meetingType'],
        section_info['meetingStart'], section_info['meetingEnd'], section_info['meetingDays'],
        section_info['meetingRoom'], section_info['meetingBuilding'], instructor_str, "None", "None", "None", section_info["sectionTitle"], crn,
        unitName  # Added this parameter
    ))
    conn.commit()
    print(f"  Course {subject} {course_number} inserted successfully.")

def update_column(conn, column_name, new_value, subject, course_num, semester, year, section_number):
    """Update a specific column in the courses table for a given section."""
    print(f"Updating column '{column_name}' for {subject} {course_num} section {section_number}...")
    conn.execute(f'''
        UPDATE courses
        SET {column_name} = ?
        WHERE subject = ? AND course_number = ? AND semester = ? AND year = ? AND sectionNumber = ?
    ''', (new_value, subject, course_num, semester, year, section_number))
    conn.commit()
    print(f"  Column '{column_name}' updated to '{new_value}'.")

# Processing Functions
def process_course(conn, year, semester, subject, course, unitName):
    """Process a single course, inserting it into the database."""
    print(f"Processing course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)
    main_info = extract_main_info(course_root)

    sections = course_root.find('sections')
    if sections is not None:
        for section in sections:
            section_url = section.get('href')
            print(f"  Processing section URL: {section_url}")
            try:
                section_root = fetch_xml(section_url)
                section_info = extract_section_info(section_root)
                insert_course(conn, year, semester, subject, course, main_info, section_info, section.get('id'), unitName)
                print(f"    Processed section: {section_info['sectionNumber']} with instructor(s): {section_info['instructor']}")
            except Exception as e:
                print(f"Error processing section for {subject} {course}: {str(e)}")
    else:
        print(f"No sections found for course: {subject} {course}")

def process_subject(conn, year, semester, subject):
    """Process all courses within a subject."""
    print(f"Processing subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)

    # Extract the unitName (department)
    unitName = safe_find(subject_root, 'unitName')
    if unitName is None:
        unitName = "Unknown Department"
        print(f"  Warning: 'unitName' not found for subject {subject}. Using 'Unknown Department'.")
    else:
        print(f"  Department (unitName): {unitName}")

    courses_element = subject_root.find('courses')
    if courses_element is not None:
        for course in courses_element:
            course_id = course.get('id')
            process_course(conn, year, semester, subject, course_id, unitName)
    else:
        print(f"No courses found for subject: {subject}")

def process_new_updates(conn, year, semester, subject, course, unitName):
    """Update existing courses with new section title information if it exists."""
    print(f"Updating course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)

    sections = course_root.find('sections')
    if sections is not None:
        for section in sections:
            section_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}/{section.get('id')}.xml"
            print(f"  Updating section URL: {section_url}")
            try:
                section_root = fetch_xml(section_url)
                section_info = extract_section_info(section_root)
                section_title = section_info['sectionTitle']

                # Update sectionTitle
                if section_title:
                    update_column(conn, "sectionTitle", section_title, subject, course, semester, year, section_info['sectionNumber'])
                    print(f"    Updated section title: {section_title}")
                else:
                    update_column(conn, "sectionTitle", "None", subject, course, semester, year, section_info['sectionNumber'])
                    print(f"    No section title found. Set to 'None'.")

                # Update CRN
                update_column(conn, "CRN", section.get('id'), subject, course, semester, year, section_info['sectionNumber'])
                print(f"    Updated CRN: {section.get('id')}")

                # Update the department (unitName)
                update_column(conn, "department", unitName, subject, course, semester, year, section_info['sectionNumber'])
                print(f"    Updated department: {unitName}")

            except Exception as e:
                print(f"Error updating section for {subject} {course}: {str(e)}")
    else:
        print(f"No sections found for course: {subject} {course}")

def process_subject_updates(conn, year, semester, subject):
    """Process updates for all courses within a subject."""
    print(f"Updating subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)

    # Extract the unitName (department)
    unitName = safe_find(subject_root, 'unitName')
    if unitName is None:
        unitName = "Unknown Department"
        print(f"  Warning: 'unitName' not found for subject {subject}. Using 'Unknown Department'.")
    else:
        print(f"  Department (unitName): {unitName}")

    courses_element = subject_root.find('courses')
    if courses_element is not None:
        for course in courses_element:
            course_id = course.get('id')
            process_new_updates(conn, year, semester, subject, course_id, unitName)
    else:
        print(f"No courses found for subject: {subject}")

# Main Functions
def main(year, semester):
    """Main function to insert data into the database."""
    print(f"Starting data insertion for {semester.capitalize()} {year}...")
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('master.db')
    create_table(conn)
    add_department_column(conn)

    subjects_element = root.find('subjects')
    if subjects_element is not None:
        for subject in subjects_element:
            process_subject(conn, year, semester, subject.get('id'))
    else:
        print("No subjects found in the schedule.")

    conn.commit()
    conn.close()
    print("Data insertion complete.")

def updating_main(year, semester):
    """Main function to update existing data in the database."""
    print(f"Starting data update for {semester.capitalize()} {year}...")
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('master.db')
    add_department_column(conn)

    subjects_element = root.find('subjects')
    if subjects_element is not None:
        for subject in subjects_element:
            process_subject_updates(conn, year, semester, subject.get('id'))
    else:
        print("No subjects found in the schedule.")

    conn.commit()
    conn.close()
    print("Data update complete.")

def update_single_course(year, semester, subject, course):
    """Update instructor information for a single course."""
    print(f"Updating single course: {subject} {course}")
    conn = sqlite3.connect('master.db')
    add_department_column(conn)

    # Extract the unitName (department) for the subject
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)
    unitName = safe_find(subject_root, 'unitName')
    if unitName is None:
        unitName = "Unknown Department"
        print(f"  Warning: 'unitName' not found for subject {subject}. Using 'Unknown Department'.")
    else:
        print(f"  Department (unitName): {unitName}")

    try:
        process_new_updates(conn, year, semester, subject, course, unitName)
        conn.commit()
    except Exception as e:
        print(f"Error updating course {subject} {course}: {e}")
    finally:
        conn.close()
        print(f"Update for course {subject} {course} complete.")


def fill_missing_departments(conn):
    """Fill missing department values in the courses table based on existing non-null department values within the same subject."""
    print("Filling missing department values...")
    cursor = conn.cursor()

    # Get a list of all subjects
    cursor.execute("SELECT DISTINCT subject FROM courses")
    subjects = [row[0] for row in cursor.fetchall()]
    
    for subject in subjects:
        # Find a non-null department value for this subject
        cursor.execute("""
            SELECT department
            FROM courses
            WHERE subject = ? AND department IS NOT NULL AND department != 'Unknown Department' AND department != ''
            LIMIT 1
        """, (subject,))
        result = cursor.fetchone()
        if result:
            department_value = result[0]
            # Now update all courses in this subject where department is NULL or 'Unknown Department' or empty string
            cursor.execute("""
                UPDATE courses
                SET department = ?
                WHERE subject = ? AND (department IS NULL OR department = '' OR department = 'Unknown Department')
            """, (department_value, subject))
            print(f"  Updated missing departments for subject {subject} to '{department_value}'")
        else:
            print(f"  No non-null department found for subject {subject}")
    conn.commit()
    print("Finished filling missing department values.")

# Entry Point
if __name__ == "__main__":

    year = "2025"
    semester = "spring"

    # Uncomment the following line to update a single course
    # update_single_course(year, semester, "CS", "498")

    # Uncomment the following line to insert data
    # main(year, semester)

    conn = sqlite3.connect('master.db')
    fill_missing_departments(conn)

    # updating_main(year, semester)

