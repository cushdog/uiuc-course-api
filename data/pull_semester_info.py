import requests
import xml.etree.ElementTree as ET
import sqlite3
import sys
import argparse
import time




# UPDATE SECTION
def update_column(conn, column_name, new_value, subject, course_num, semester, year):
    conn.execute(f"UPDATE courses SET {column_name} = ? WHERE subject = ? AND course_number = ? AND semester = ? AND year = ?", (new_value,subject,course_num,semester,year,))

def process_new_updates(conn, year, semester, subject, course):
    print(f"Processing course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)
    main_info = extract_main_info(course_root)

    for section in course_root.find('sections'):
        section_url = section.get('href')
        try:
            section_root = fetch_xml(section_url)
            section_info = extract_section_info(section_root)

            section_info['instructor'] = ', '.join(section_info['instructor']) if section_info['instructor'] else None

            update_column(conn, "instructor", section_info['instructor'], subject, course, semester, year)
            print(f"  Processed section: {section_info['sectionNumber']}")
        except Exception as e:
            print(f"Error processing section for {subject} {course}: {str(e)}")

def process_subject_updates(conn, year, semester, subject):
    print(f"Processing subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)
    
    for course in subject_root.find('courses'):
        course_id = course.get('id')
        process_new_updates(conn, year, semester, subject, course_id)

def updating_main(year, semester):
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('master.db')

    for subject in root.find('subjects'):
        subject_id = subject.get('id')
        process_subject_updates(conn, year, semester, subject_id)

    conn.commit()
    conn.close()


# END UPDATE SECTION




















def fetch_xml(url):
    response = requests.get(url)
    return ET.fromstring(response.content)

def safe_find(root, element):
    found = root.find(element)
    return found.text if found is not None else None

def extract_main_info(root):
    info = {}
    info['label'] = safe_find(root, 'label')
    info['description'] = safe_find(root, 'description')
    info['creditHours'] = safe_find(root, 'creditHours')
    return info

def extract_section_info(root):
    info = {}
    info['sectionNumber'] = safe_find(root, 'sectionNumber')
    info['statusCode'] = safe_find(root, 'statusCode')
    info['sectionText'] = safe_find(root, 'sectionText')
    info['sectionNotes'] = safe_find(root, 'sectionNotes')
    info['sectionCappArea'] = safe_find(root, 'sectionCappArea')
    info['enrollmentStatus'] = safe_find(root, 'enrollmentStatus')
    info['startDate'] = safe_find(root, 'startDate')
    info['endDate'] = safe_find(root, 'endDate')
    
    meetings = root.find('meetings')
    if meetings is not None and len(meetings) > 0:
        meeting = meetings[0]
        info['meetingType'] = safe_find(meeting, 'type')
        info['meetingStart'] = safe_find(meeting, 'start')
        info['meetingEnd'] = safe_find(meeting, 'end')
        info['meetingDays'] = safe_find(meeting, 'daysOfTheWeek')
        info['meetingRoom'] = safe_find(meeting, 'roomNumber')
        info['meetingBuilding'] = safe_find(meeting, 'buildingName')
        
        instructors = meeting.find('instructors')
        if instructors is not None and len(instructors) > 0:
            info['instructor'] = [instructor.text for instructor in instructors]
        else:
            info['instructor'] = None
    else:
        info['meetingType'] = info['meetingStart'] = info['meetingEnd'] = info['meetingDays'] = info['meetingRoom'] = info['meetingBuilding'] = info['instructor'] = None
    
    return info

def create_table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS courses
                 (year INTEGER, semester TEXT, subject TEXT, course_number TEXT, 
                 label TEXT, description TEXT, creditHours TEXT,
                 sectionNumber TEXT, statusCode TEXT, sectionText TEXT, 
                 sectionNotes TEXT, sectionCappArea TEXT, enrollmentStatus TEXT,
                 startDate TEXT, endDate TEXT, meetingType TEXT, meetingStart TEXT,
                 meetingEnd TEXT, meetingDays TEXT, meetingRoom TEXT,
                 meetingBuilding TEXT, instructor TEXT)''')

def insert_course(conn, year, semester, subject, course_number, main_info, section_info):
    instructor_str = ', '.join(section_info['instructor']) if section_info['instructor'] else None
    conn.execute('''INSERT INTO courses VALUES 
                 (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                 (year, semester, subject, course_number, 
                  main_info['label'], main_info['description'], main_info['creditHours'],
                  section_info['sectionNumber'], section_info['statusCode'], section_info['sectionText'],
                  section_info['sectionNotes'], section_info['sectionCappArea'], section_info['enrollmentStatus'],
                  section_info['startDate'], section_info['endDate'], section_info['meetingType'],
                  section_info['meetingStart'], section_info['meetingEnd'], section_info['meetingDays'],
                  section_info['meetingRoom'], section_info['meetingBuilding'], instructor_str))
    

def process_course(conn, year, semester, subject, course):
    print(f"Processing course: {subject} {course}")
    course_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}/{course}.xml"
    course_root = fetch_xml(course_url)
    main_info = extract_main_info(course_root)

    for section in course_root.find('sections'):
        section_url = section.get('href')
        try:
            section_root = fetch_xml(section_url)
            section_info = extract_section_info(section_root)
            insert_course(conn, year, semester, subject, course, main_info, section_info)
            print(f"  Processed section: {section_info['sectionNumber']}")
        except Exception as e:
            print(f"Error processing section for {subject} {course}: {str(e)}")

def process_subject(conn, year, semester, subject):
    print(f"Processing subject: {subject}")
    subject_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}/{subject}.xml"
    subject_root = fetch_xml(subject_url)
    
    for course in subject_root.find('courses'):
        course_id = course.get('id')
        process_course(conn, year, semester, subject, course_id)

def main(year, semester):
    base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/{year}/{semester}.xml"
    root = fetch_xml(base_url)

    conn = sqlite3.connect('master.db')
    create_table(conn)

    for subject in root.find('subjects'):
        subject_id = subject.get('id')
        process_subject(conn, year, semester, subject_id)

    conn.commit()
    conn.close()

if __name__ == "__main__":

    year = "2024"
    semester = "fall"
    
    updating_main(year, semester)










