from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/search": {"origins": "http://localhost:3000"}})  # Enabling CORS for the search route

DATABASE = 'master.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    words = query.split()
    if len(words) == 1:
        class_name = words[0].upper()
        return jsonify(search_and_format_subject(class_name))
    else:
        class_name, course_number = words[0].upper(), words[1]
        return jsonify(search_and_format(class_name, course_number))

def pull_from_table(class_name, course_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM classes WHERE subject = ? AND number = ?;"
    cursor.execute(query, (class_name, course_number))
    results = cursor.fetchall()
    conn.close()
    if not results:
        return "Course not found"
    return results[0]

def search_and_format(class_name, course_number):
    info_list = pull_from_table(class_name, course_number)
    return info_list

def search_and_format_subject(class_name):
    info_list = pull_from_table(class_name)
    return info_list

def pull_from_table_subject(class_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM classes WHERE subject = ?;"
    cursor.execute(query, (class_name,))
    results = cursor.fetchall()
    conn.close()
    if not results:
        return "Course not found"
    return results

if __name__ == '__main__':
    app.run(debug=True)