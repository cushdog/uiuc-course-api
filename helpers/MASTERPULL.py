import requests
import xml.etree.ElementTree as ET
import sqlite3
import time

# Helper Functions
def fetch_xml(url):
    """Fetch XML content from a URL and parse it."""
    response = requests.get(url)
    return ET.fromstring(response.content)

def safe_find(root, element):
    """Safely find an element in XML and return its text."""
    found = root.find(element)
    return found.text if found is not None else None

# Data Extraction Functions
def extract_main_info(root):
    """Extract main course information."""
    return {
        'label': safe_find(root, 'label'),
        'description': safe_find(root, 'description'),
        'creditHours': safe_find(root, 'creditHours')
    }

def extract_section_info(root):
    """Extract section information, including all instructors."""

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
                for instructor in instructors:
                    if instructor.text:
                        instructors_set.add(instructor.text)

    info['instructor'] = list(instructors_set) if instructors_set else None
    return info

# Database Functions
def create_table(conn):
    """Create the courses table if it doesn't exist."""
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
            instructor TEXT
        )
    ''')

def insert_course(conn, year, semester, subject, course_number, main_info, section_info, crn):
    """Insert a new course record into the database."""
    instructor_str = ', '.join(section_info['instructor']) if section_info['instructor'] else None
    conn.execute('''
        INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        year, semester, subject, course_number,
        main_info['label'], main_info['description'], main_info['creditHours'],
        section_info['sectionNumber'], section_info['statusCode'], section_info['sectionText'],
        section_info['sectionNotes'], section_info['sectionCappArea'], section_info['enrollmentStatus'],
        section_info['startDate'], section_info['endDate'], section_info['meetingType'],
        section_info['meetingStart'], section_info['meetingEnd'], section_info['meetingDays'],
        section_info['meetingRoom'], section_info['meetingBuilding'], instructor_str, "None", "None", "None", "None", crn
    ))
    conn.commit()

def update_column(conn, column_name, new_value, subject, course_num, semester, year, section_number):
    """Update a specific column in the courses table for a given section."""
    conn.execute(f'''
        UPDATE courses
        SET {column_name} = ?
        WHERE subject = ? AND course_number = ? AND semester = ? AND year = ? AND sectionNumber = ?
    ''', (new_value, subject, course_num, semester, year, section_number))

# Processing Functions
def process_course(conn, year, semester, subject, course):
    """Process a single course, inserting it into the database."""
    print(f"Processing course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)
    main_info = extract_main_info(course_root)

    for section in course_root.find('sections'):
        section_url = section.get('href')
        try:
            section_root = fetch_xml(section_url)
            section_info = extract_section_info(section_root)
            insert_course(conn, year, semester, subject, course, main_info, section_info, section.get('id'))
            print(f"  Processed section: {section_info['sectionNumber']} with instructor(s): {section_info['instructor']}")
        except Exception as e:
            print(f"Error processing section for {subject} {course}: {str(e)}")

def process_subject(conn, year, semester, subject):
    """Process all courses within a subject."""
    print(f"Processing subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)

    for course in subject_root.find('courses'):
        course_id = course.get('id')
        process_course(conn, year, semester, subject, course_id)

def process_new_updates(conn, year, semester, subject, course):
    """Update existing courses with new section title information if it exists."""
    print(f"Updating course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)

    for section in course_root.find('sections'):
        section_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}/{section.get('id')}.xml"
        try:

            section_root = fetch_xml(section_url)
            section_info = extract_section_info(section_root)
            section_title = section_info['sectionTitle']

            # Only update if sectionTitle exists
            if section_title:
                update_column(conn, "sectionTitle", section_title, subject, course, semester, year, section_info['sectionNumber'])
                print(f"  Updated section: {section_info['sectionNumber']} with section title: {section_title}")
            else:
                update_column(conn, "sectionTitle", "None", subject, course, semester, year, section_info['sectionNumber'])
                print(f"  Skipping section: {section_info['sectionNumber']} - no section title found")

            update_column(conn, "CRN", section.get('id'), subject, course, semester, year, section_info['sectionNumber'])
            print(f"  Updated CRN for section: {section_info['sectionNumber']} with CRN: {section.get('id')}")

        except Exception as e:
            print(f"Error updating section for {subject} {course}: {str(e)}")

def process_subject_updates(conn, year, semester, subject):
    """Process updates for all courses within a subject."""
    print(f"Updating subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)

    for course in subject_root.find('courses'):
        course_id = course.get('id')
        process_new_updates(conn, year, semester, subject, course_id)

# Main Functions
def main(year, semester):
    """Main function to insert data into the database."""
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('../data/DB/master.db')
    create_table(conn)

    for subject in root.find('subjects'):
        subject_id = subject.get('id')
        process_subject(conn, year, semester, subject_id)

    conn.commit()
    conn.close()

def updating_main(year, semester):
    """Main function to update existing data in the database."""
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('../data/DB/master.db')

    for subject in root.find('subjects'):
        subject_id = subject.get('id')
        process_subject_updates(conn, year, semester, subject_id)

    conn.commit()
    conn.close()

def update_single_course(year, semester, subject, course):
    """Update instructor information for a single course."""
    conn = sqlite3.connect('../data/DB/master.db')

    try:
        process_new_updates(conn, year, semester, subject, course)
        conn.commit()
    except Exception as e:
        print(f"Error updating course {subject} {course}: {e}")
    finally:
        conn.close()

# Entry Point
if __name__ == "__main__":
    year = "2025"
    semester = "spring"

    conn = sqlite3.connect('../data/DB/master.db')

    process_course(conn, year, semester, "CS", "173")

    # Uncomment the following line to update a single course
    # update_single_course(year, semester, "CS", "498")

    # Uncomment the following line to insert data
    # main(year, semester)