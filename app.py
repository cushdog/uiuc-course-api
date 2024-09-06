from flask import Flask, request, jsonify
from seat_search import perform_search
import xml.etree.ElementTree as ET
from flask_cors import CORS
import requests
import sqlite3
import csv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DATABASE = 'master.db'

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

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
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
    with open('subject_ids.txt', 'r') as file:
        data = file.read()
    return data

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

if __name__ == '__main__':
    app.run(debug=True)
