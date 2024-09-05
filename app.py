from flask import Flask, request, jsonify
from seat_search import perform_search
import xml.etree.ElementTree as ET
from flask_cors import CORS
import requests
import sqlite3
import csv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:8080", "https://course-explorer-electric-boogaloo.vercel.app"]}})

DATABASE = 'master.db'

def parse_xml_to_json(xml_content):
    # Parse the XML content
    root = ET.fromstring(xml_content)
    
    # Create a dictionary to hold the parsed data
    result = {}

    # Get subject attributes
    result['id'] = root.attrib.get('id', None)

    # Parse the <label> element (subject full name)
    label = root.find('{http://rest.cis.illinois.edu}label')
    if label is not None:
        result['label'] = label.text

    # Parse <collegeCode>, <departmentCode>, and other simple fields
    result['collegeCode'] = root.find('{http://rest.cis.illinois.edu}collegeCode').text if root.find('{http://rest.cis.illinois.edu}collegeCode') is not None else None
    result['departmentCode'] = root.find('{http://rest.cis.illinois.edu}departmentCode').text if root.find('{http://rest.cis.illinois.edu}departmentCode') is not None else None
    result['unitName'] = root.find('{http://rest.cis.illinois.edu}unitName').text if root.find('{http://rest.cis.illinois.edu}unitName') is not None else None
    result['contactName'] = root.find('{http://rest.cis.illinois.edu}contactName').text if root.find('{http://rest.cis.illinois.edu}contactName') is not None else None
    result['contactTitle'] = root.find('{http://rest.cis.illinois.edu}contactTitle').text if root.find('{http://rest.cis.illinois.edu}contactTitle') is not None else None
    result['addressLine1'] = root.find('{http://rest.cis.illinois.edu}addressLine1').text if root.find('{http://rest.cis.illinois.edu}addressLine1') is not None else None
    result['addressLine2'] = root.find('{http://rest.cis.illinois.edu}addressLine2').text if root.find('{http://rest.cis.illinois.edu}addressLine2') is not None else None
    result['phoneNumber'] = root.find('{http://rest.cis.illinois.edu}phoneNumber').text if root.find('{http://rest.cis.illinois.edu}phoneNumber') is not None else None
    result['webSiteURL'] = root.find('{http://rest.cis.illinois.edu}webSiteURL').text if root.find('{http://rest.cis.illinois.edu}webSiteURL') is not None else None

    # Parse courses and add them to the result
    courses = []
    for course in root.findall('{http://rest.cis.illinois.edu}courses/{http://rest.cis.illinois.edu}course'):
        courses.append({
            'id': course.attrib.get('id'),
            'href': course.attrib.get('href'),
            'title': course.text
        })
    result['courses'] = courses

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
        json_data = parse_xml_to_json(xml_content)
        return jsonify(json_data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)