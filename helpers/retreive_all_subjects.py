import xml.etree.ElementTree as ET
import requests
import sqlite3
import json
import csv


DATABASE = '../data/DB/master.db'
semester = 'fall'
year = '2024'

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

def get_subject_names():

    query = "SELECT DISTINCT subject FROM courses WHERE semester = ? AND year = ?;"
    params = (semester, year)

    results = execute_query(query, params)
    flattened_result = [item[0] for item in results]

    
    return flattened_result

def get_real_subject_names():
    
    subject_names = get_subject_names()

    for subject in subject_names:
        
        base_url = f"https://courses.illinois.edu/cisapp/explorer/schedule/2024/fall/{subject}.xml"

        response = requests.get(base_url)

        # Parse the XML content
        root = ET.fromstring(response.content)

        # Find the 'label' tag in the XML
        label = root.find('.//label')

        # Print the label text if it exists
        if label is not None:
            print(label.text)

            # output subject,label to csv
            with open('subject_label.csv', mode='a') as file:
                writer = csv.writer(file)
                writer.writerow([subject, label.text])
        else:
            print('Label not found.')

get_real_subject_names()
