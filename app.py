from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Simplified CORS; adjust as necessary for your deployment scenario

DATABASE = 'master.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Important for enabling dictionary-like access to row results
    return conn

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    words = query.split()
    if len(words) == 2:  # Format like "CS 415"
        subject, number = words
        cursor.execute("SELECT * FROM classes WHERE subject = ? AND number = ?", (subject.upper(), number))
    else:  # Format like "CS" for subject search
        subject = words[0]
        cursor.execute("SELECT * FROM classes WHERE subject = ?", (subject.upper(),))

    results = cursor.fetchall()
    conn.close()
    # Convert fetched data to a list of dicts
    results_list = [dict(row) for row in results] if results else []
    return jsonify(results_list)

if __name__ == '__main__':
    app.run(debug=True)
