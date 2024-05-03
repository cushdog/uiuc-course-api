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
    conn = get_db_connection()
    cursor = conn.cursor()
    words = query.split()
    if len(words) == 2:  # Assuming a format like "CS 415"
        subject, number = words
        cursor.execute("SELECT * FROM classes WHERE subject = ? AND number = ?", (subject, number))
    else:  # Assuming a format like "CS" for subject search
        subject = words[0]
        cursor.execute("SELECT * FROM classes WHERE subject = ?", (subject,))
    results = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])


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

if __name__ == '__main__':
    app.run(debug=True)
