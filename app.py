from flask import Flask, request, jsonify
from helpers.seat_search import perform_search
from helpers.general_helpers import search_teacher
import xml.etree.ElementTree as ET
from flask_cors import CORS
import requests
import sqlite3
import json
import csv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DATABASE = 'data/DB/master.db'
AVG_GPA_DATABASE = 'data/DB/professor_stats.db'
GPA_STATS_DATABASE = 'data/DB/gpa.db'

def parse_course_catalog(xml_content):
    # Parse the XML content
    root = ET.fromstring(xml_content)
    
    # Create a dictionary to hold the parsed data
    result = {}

    # Extract subject attributes
    result['id'] = root.attrib.get('id')

    # Extract simple fields
    simple_fields = [
        'label', 'collegeCode', 'departmentCode', 'unitName', 'contactName',
        'contactTitle', 'addressLine1', 'addressLine2', 'phoneNumber',
        'webSiteURL', 'collegeDepartmentDescription'
    ]
    for field in simple_fields:
        element = root.find(f'.//{field}')
        result[field] = element.text if element is not None else None

    # Extract parents information
    parents = root.find('.//parents')
    if parents is not None:
        result['parents'] = {}
        for parent in parents:
            result['parents'][parent.tag] = {
                'id': parent.attrib.get('id'),
                'href': parent.attrib.get('href'),
                'text': parent.text
            }

    # Extract courses
    courses = root.find('.//courses')
    if courses is not None:
        result['courses'] = []
        for course in courses:
            result['courses'].append({
                'id': course.attrib.get('id'),
                'href': course.attrib.get('href'),
                'title': course.text
            })

    return result

def parse_course_xml(xml_content):
    # Parse the XML content
    root = ET.fromstring(xml_content)
    
    # Create a dictionary to hold the parsed data
    result = {}

    # Extract course attributes
    result['id'] = root.attrib.get('id')

    # Extract parents information
    parents = root.find('parents')
    if parents is not None:
        result['parents'] = {}
        for parent in parents:
            result['parents'][parent.tag] = parent.text

    # Extract simple fields
    simple_fields = [
        'label', 'description', 'creditHours', 'sectionDegreeAttributes'
    ]
    for field in simple_fields:
        element = root.find(f'./{field}')
        if element is not None and element.text:
            result[field] = element.text.strip()

    # Extract genEdCategories
    gen_ed_categories = root.find('genEdCategories')
    if gen_ed_categories is not None:
        result['genEdCategories'] = []
        for category in gen_ed_categories.findall('category'):
            cat_info = {
                'description': category.find('description').text.strip() if category.find('description') is not None else None,
            }
            attributes = category.find('.//genEdAttributes')
            if attributes is not None:
                for attr in attributes.findall('genEdAttribute'):
                    cat_info['genEdAttribute'] = attr.text.strip()
            result['genEdCategories'].append(cat_info)

    # Extract sections
    sections = root.find('sections')
    if sections is not None:
        result['sections'] = [section.text for section in sections if section.text]

    return result

def execute_query(query, params):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_gpa_query(query, params):
    conn = get_gpa_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_gpa_stats_query(query, params):
    conn = get_gpa_stats_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def get_gpa_db_connection():
    conn = sqlite3.connect(AVG_GPA_DATABASE)
    return conn

def get_gpa_stats_connection():
    conn = sqlite3.connect(GPA_STATS_DATABASE)
    return conn

@app.route('/prof-search', methods=['GET'])
def profSearch():
    query = request.args.get('query')
    words = query.split()

    last_name, semester, year = words[0], words[1], words[2]

    query = """
        SELECT DISTINCT *
        FROM courses
        WHERE instructor LIKE ?
        AND semester = ?
        AND year = ?
    """
    params = ('%' + last_name + '%', semester, year)
    return jsonify(execute_query(query, params))

@app.route('/gpa-search', methods=['GET'])
def gpaSearch():
    query = request.args.get('query')
    words = query.split()
    query = """SELECT * FROM courses WHERE subject = ? AND course_number = ?;"""
    params = (words[0].upper(), words[1])
    return jsonify(execute_query(query, params))

@app.route('/master-search', methods=['GET'])
def readFile():

    query = request.args.get('query')
    words = query.split()
    semester, year = words[0], words[1]

    query = "SELECT DISTINCT subject FROM courses WHERE semester = ? AND year = ?;"
    params = (semester, year)

    results = execute_query(query, params)
    flattened_result = [item[0] for item in results]

    return jsonify(flattened_result)

@app.route('/interest-search', methods=['GET'])
def interest():
    query = request.args.get('query')
    with open('areas_of_interest.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == query:
                return row
    return None

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    words = query.split()
    if len(words) == 3:
        query = """SELECT * FROM courses WHERE subject = ? AND semester = ? AND year = ?;"""
        params = (words[0].upper(), words[1], words[2])
        return jsonify(execute_query(query, params))
    else:
        query = "SELECT * FROM courses WHERE subject = ? AND course_number = ? AND semester = ? AND year = ?;"
        params = (words[0].upper(), words[1], words[2], words[3])
        return jsonify(execute_query(query, params)[0])

@app.route('/prereq-search', methods=['GET'])
def prereq_search():
    course = request.args.get('course')
    query = "SELECT * FROM courses WHERE description LIKE ?"
    return jsonify(execute_query(query, (f'%{course}%',)))

@app.route('/sections', methods=['GET'])
def sections():
    query = request.args.get('query')
    words = query.split()

    query = "SELECT * FROM courses WHERE subject = ? AND course_number = ? AND semester = ? AND year = ?;"
    params = (words[0].upper(), words[1], words[2], words[3])

    return jsonify(execute_query(query, params))

@app.route('/description', methods=['GET'])
def description_search():

    query = request.args.get('query')
    term = request.args.get('term')
    semester, year = term.split()

    sql_query = "SELECT * FROM courses WHERE label LIKE ? AND semester = ? AND year = ?"
    params = (f'%{query}%', semester, year)

    return jsonify(execute_query(sql_query, params))

@app.route('/seat-search', methods=['GET'])
def seat_search():
    query = request.args.get('query')
    words = query.split()
    class_name, course_number = words[0].upper(), words[1]
    results = perform_search(class_name, course_number)
    return jsonify(results)

@app.route('/subject-info', methods=['GET'])
def subject_info():
    subject = request.args.get('subject')
    if not subject:
        return jsonify({'error': 'Missing subject parameter'}), 400

    # Construct the URL
    url = f'https://courses.illinois.edu/cisapp/explorer/schedule/2024/fall/{subject}.xml'

    try:
        # Fetch the XML content
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for 4xx/5xx responses
        xml_content = response.text

        # Parse the XML content and return it as JSON
        json_data = parse_course_catalog(xml_content)
        return jsonify(json_data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/class-info', methods=['GET'])
def class_info():

    query = request.args.get('class')
    words = query.split()
    subject, class_num = words[0].upper(), words[1]

    if not query:
        return jsonify({'error': 'Missing parameter'}), 400

    # Construct the URL
    url = f'https://courses.illinois.edu/cisapp/explorer/schedule/2024/fall/{subject}/{class_num}.xml'

    try:

        # Fetch the XML content
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for 4xx/5xx responses
        xml_content = response.text

        # Parse the XML content and return it as JSON
        json_data = parse_course_xml(xml_content)
        return jsonify(json_data)
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/old-api', methods=['GET'])
def oldApi():

    query = request.args.get('query')
    words = query.split()
    subject, class_num, field = words[0].upper(), words[1], words[2]

    query = "SELECT DISTINCT * FROM courses WHERE subject = ? AND course_number = ? AND semester = 'fall' AND year = 2024;"
    params = (subject, class_num)

    results = execute_query(query, params)[0]
    old_api_data = json.loads(results[-1])

    result_string = "None"

    if field in old_api_data:
        result_string = old_api_data[field]

    return jsonify(result_string)

@app.route('/requirements', methods=['GET'])
def requirementsSearch():

    search_t = request.args.get('query')

    query = "SELECT DISTINCT * FROM courses WHERE ATTRIBUTES LIKE ? AND semester = 'fall' AND year = 2024;"
    params = ('%' + search_t + '%',)

    print("QUERY: ", search_t)

    results = execute_query(query, params)

    result_string = "None"

    if results is not None:
        return jsonify(results)
    
    return jsonify(result_string)

@app.route('/rmp', methods=['GET'])
def rmpSearch():

    query = request.args.get('query')
    words = query.split()
    first_name, last_name = words[0], words[1]

    return jsonify(search_teacher(first_name, last_name))

@app.route('/crn-search', methods=['GET'])
def crn_search():
    crn = request.args.get('crn')
    query = "SELECT * FROM courses WHERE crn = ? AND semester = 'fall' AND year = 2024;"
    return jsonify(execute_query(query, (crn,))[0])

@app.route('/subject-names', methods=['GET'])
def subject_names():
    subjects = []
    with open('data/CSVs/subject_names.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            subjects.append({'code': row[0], 'name': row[1]})
    return jsonify(subjects)

@app.route('/class-average-gpas', methods=['GET'])
def updated_average_gpas():
    subject = request.args.get('subject', None)
    course_number = request.args.get('course_number', None)
    course = subject + ' ' + course_number if subject and course_number else None
    
    # Build the base SQL query
    query = "SELECT class, avg_gpa FROM class_stats WHERE class = ?"
    params = (course,)
    
    # Execute the query
    results = execute_gpa_query(query, params)
    
    # Format the results into a JSON structure
    gpa_data = []
    for row in results:
        gpa_data.append({
            "class": row[0],
            "average_gpa": row[1]
        })
    return jsonify(gpa_data)

@app.route('/professor-stats', methods=['GET'])
def professor_stats():
    # Optional parameters to filter by professor name or class
    class_name = request.args.get('class', None)
    
    # Build the base SQL query
    query = "SELECT class, professor, avg_gpa, total_students FROM professor_stats WHERE class = ?"
    params = (class_name,)
    
    # Execute the query
    results = execute_gpa_query(query, params)
    
    # Format the results into a JSON structure
    professor_data = []
    for row in results:
        professor_data.append({
            "class": row[0],
            "professor": row[1],
            "average_gpa": row[2],
            "total_students": row[3]
        })
    
    return jsonify(professor_data)

@app.route('/gpa-distribution', methods=['GET'])
def gpa_distribution():
    class_name = request.args.get('class', None)

    subject, course_number = class_name.split()
    
    # Build the base SQL query
    query = "SELECT percentAplus, percentA, percentAminus, percentBplus, percentB, percentBminus, percentCplus, percentC, percentCminus, percentDplus, percentD, percentDminus, percentF FROM classes WHERE subject = ? AND number = ?"
    params = (subject, course_number)
    
    return jsonify(execute_gpa_stats_query(query, params))

@app.route('/name-search', methods=['GET'])
def professor_search():
    # Get query parameters
    department = request.args.get('department', '').lower()
    last_name = request.args.get('last_name', '').lower()

    if not department or not last_name:
        return jsonify({'error': 'Please provide both department and last_name parameters.'}), 400
    
    # Load the JSON data once when the application starts
    with open('./data/Other/professors.json', 'r') as json_file:
        professor_data = json.load(json_file)['data']

    # Search for matching professors
    matching_professors = []
    for prof in professor_data:
        prof_department = prof.get('departmentname', '').lower()
        prof_last_name = prof.get('lastname', '').lower()
        if department in prof_department and last_name == prof_last_name:
            matching_professors.append(prof)

    if not matching_professors:
        return jsonify({'message': 'No matching professors found.'}), 404

    return jsonify(matching_professors)

if __name__ == '__main__':
    app.run(debug=True)
