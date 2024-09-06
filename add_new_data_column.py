from flask import Flask, request, jsonify
from seat_search import perform_search
import xml.etree.ElementTree as ET
from flask_cors import CORS
import requests
import sqlite3
import csv
import pandas as pd
import json

DATABASE = 'master.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def execute_query(query, params):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

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

def class_info(subject, class_num):

    # Construct the URL
    url = f'https://courses.illinois.edu/cisapp/explorer/schedule/2024/fall/{subject}/{class_num}.xml'

    try:
        # Fetch the XML content
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for 4xx/5xx responses
        xml_content = response.text

        # Parse the XML content and return it as JSON
        json_data = parse_course_xml(xml_content)
        return json_data
    except requests.exceptions.RequestException as e:
        return str(e)

# Function to add the "OLD API DATA" column if it doesn't exist and update the rows
def update_section_attributes():
    # Connect to the SQLite database
    conn = sqlite3.connect('master.db')
    cursor = conn.cursor()

    # Add the "OLD API DATA" column if it doesn't exist
    cursor.execute("""
        ALTER TABLE courses ADD COLUMN "OLD API DATA" TEXT;
    """)
    conn.commit()

    # Query all classes from the 'courses' table where the year is 2024 and semester is 'fall'
    cursor.execute("SELECT subject, course_number FROM courses WHERE year = '2024' AND semester = 'fall'")
    classes = cursor.fetchall()

    for subject, class_num in classes:
        print(f"Fetching data for {subject} {class_num}...")
        # Fetch class information
        class_data = class_info(subject, class_num)
        
        # Convert the JSON data to a string to store it in the database
        class_data_json = json.dumps(class_data)

        # Update the corresponding row in the database with the full JSON data
        cursor.execute("""
            UPDATE courses
            SET "OLD API DATA" = ?
            WHERE subject = ? AND course_number = ? AND year = '2024' AND semester = 'fall'
        """, (class_data_json, subject, class_num))
        conn.commit()

    # Close the database connection
    conn.close()

update_section_attributes()