from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://course-explorer-electric-boogaloo.vercel.app"]}})

DATABASE = 'master.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def pull_from_table(class_name, course_number, semester, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM classes WHERE subject = ? AND number = ? AND term = ? AND year = ?;"
    cursor.execute(query, (class_name, course_number, semester, year))
    results = cursor.fetchall()
    conn.close()
    if not results:
        return "Course not found"
    return results[0]

def search_and_format(class_name, course_number, semester, year):
    info_list = pull_from_table(class_name, course_number, semester, year)
    return info_list

def search_and_format_subject(class_name, semester, year):
    info_list = pull_from_table_subject(class_name, semester, year)
    return info_list

def pull_from_table_subject(class_name, semester, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM classes 
    WHERE subject = ? AND term = ? AND year = ?;
    """
    cursor.execute(query, (class_name, semester, year,))
    results = cursor.fetchall()
    conn.close()
    if not results:
        return "Course not found"
    return results

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    words = query.split()
    if len(words) == 3:
        class_name = words[0].upper()
        semester, year = words[1], words[2]
        return jsonify(search_and_format_subject(class_name, semester, year))
    else:
        class_name, course_number = words[0].upper(), words[1]
        semester, year = words[2], words[3]
        print("Class name: " + class_name)
        print("Course number: " + str(course_number))
        return jsonify(search_and_format(class_name, course_number, semester, year))

@app.route('/prereq-search', methods=['GET'])
def prereq_search():
    course = request.args.get('course')
    results = search_prereqs(course)
    return jsonify(results)

def search_prereqs(course):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM classes WHERE section_info LIKE ?"
    cursor.execute(query, (f'%{course}%',))
    results = cursor.fetchall()
    conn.close()
    return results



if __name__ == '__main__':
    app.run(debug=True)
