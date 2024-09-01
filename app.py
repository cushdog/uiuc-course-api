from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import csv
from seat_search import perform_search

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:8080", "https://course-explorer-electric-boogaloo.vercel.app"]}})

DATABASE = 'master.db'

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

if __name__ == '__main__':
    app.run(debug=True)