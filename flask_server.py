from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = '/Users/tylercushing/Desktop/code stuff/course explorer directors cut/uiuc-course-bot-redux-main/master.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    words = query.split()
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

if __name__ == '__main__':
    app.run(debug=True)
