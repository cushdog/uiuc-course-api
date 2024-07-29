from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import re

app = Flask(__name__)
CORS(app, resources={r"/search": {"origins": ["http://localhost:3000", "https://course-explorer-electric-boogaloo.vercel.app"]}})  # Enabling CORS for the search route

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    query = re.sub(r'(\D)(\d)', r'\1 \2', query)
    words = query.split()
    
    class_name, course_number = words[0].upper(), words[1]
    return jsonify(make_request(class_name, course_number))
        
def make_request(subject, course_num):
    # Request URL
    url = "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/searchResults/searchResults"

    # Query parameters
    params = {
        "txt_subject": subject,
        "txt_courseNumber": course_num,
        "txt_term": "120248",
        "startDatepicker": "",
        "endDatepicker": "",
        "uniqueSessionId": "r5lks1722222298105",
        "pageOffset": "0",
        "pageMaxSize": "100",
        "sortColumn": "subjectDescription",
        "sortDirection": "asc"
    }

    # Request headers
    headers = {
        "ADRUM": "isAjax:true",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Cookie": "JSESSIONID=E8F6C514E4A83D65BDC2B999632AAC2B.server10; _ga=GA1.1.1572162851.1722216584; OptanonAlertBoxClosed=2024-07-29T03:03:35.027Z; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Jul+28+2024+22%3A03%3A35+GMT-0500+(Central+Daylight+Time)&version=6.39.0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1; _ga_xxxxxxxxx=GS1.1.1722222213.2.0.1722222215.0.0.0; _ga_Z2Y1R5M3ML=GS1.1.1722222213.2.0.1722222215.0.0.0; ADRUM=s~1722222329190&r~aHR0cHMlM0ElMkYlMkZiYW5uZXIuYXBwcy51aWxsaW5vaXMuZWR1JTJGU3R1ZGVudFJlZ2lzdHJhdGlvblNTQiUyRnNzYiUyRmNsYXNzUmVnaXN0cmF0aW9u",
        "DNT": "1",
        "Host": "banner.apps.uillinois.edu",
        "Referer": "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/classRegistration/classRegistration",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "X-Synchronizer-Token": "c11e0f03-7fb0-4f1e-a6d0-5eac72e440dd",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\""
    }

    # Making the GET request
    response = requests.get(url, headers=headers, params=params)

    list_to_return = []

    # Checking the response
    if response.status_code == 200:
        data = response.json()
        sections = data.get('data', [])
        
        for section in sections:

            section_id = section.get('id')
            course_number = section.get('courseNumber')
            subject = section.get('subject')
            title = section.get('courseTitle')
            seats_available = section.get('seatsAvailable')
            maximum_enrollment = section.get('maximumEnrollment')
            enrollment = section.get('enrollment')

            tuple_to_append = (section_id, subject, course_number, title, seats_available, maximum_enrollment, enrollment)
            list_to_return.append(tuple_to_append)

    else:
        print(f"Request failed with status code {response.status_code}")

if __name__ == '__main__':
    app.run(debug=True)
