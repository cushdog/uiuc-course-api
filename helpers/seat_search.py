from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
import requests
import boto3
import json
import uuid
import os

def get_secret():

    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    secret_name = "CourseExplorerCookie"
    region_name = "us-east-1"
    
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:

        raise e

    secret = json.loads(get_secret_value_response['SecretString'])

    return secret[secret_name]

def generate_unique_session_id():
    return str(uuid.uuid4().hex[:12]) + str(uuid.uuid4().hex[:12])

def get_synchronizer_token(session):
    url = "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/registration?mepCode=1UIUC"
    response = session.get(url)

    print(response.text)
    
    # Parse the response to find the synchronizer token
    soup = BeautifulSoup(response.text, 'html.parser')
    token_meta = soup.find('meta', {'name': 'synchronizerToken'})
    
    if token_meta:
        return token_meta['content']
    else:
        raise Exception("Synchronizer token not found")

def reset_search(session, token, cookie):
    reset_url = "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/classSearch/resetDataForm"
    
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Cookie": cookie,  # Added the Cookie header
        "Origin": "https://banner.apps.uillinois.edu",
        "Priority": "u=3, i",  # New header added
        "Referer": "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/classRegistration/classRegistration",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        "X-Requested-With": "XMLHttpRequest",
        "X-Synchronizer-Token": token
    }
    
    response = session.post(reset_url, headers=headers)
    return response

def make_search_request(session, token, subject, course_num, cookie):
    search_url = "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/searchResults/searchResults"
    unique_session_id = generate_unique_session_id()
    
    params = {
        "txt_subject": subject,
        "txt_courseNumber": course_num,
        "txt_term": "120248",
        "startDatepicker": "",
        "endDatepicker": "",
        "uniqueSessionId": unique_session_id,
        "pageOffset": "0",
        "pageMaxSize": "10",  # Updated to match the provided parameters
        "sortColumn": "subjectDescription",
        "sortDirection": "asc"
    }
    
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Cookie": cookie,
        "Priority": "u=3, i",  # New header added
        "Referer": "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/classRegistration/classRegistration",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        "X-Requested-With": "XMLHttpRequest",
        "X-Synchronizer-Token": token
    }
    
    response = session.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed: {response.text}")
        return None

def perform_search(subject, course_num):
    session = requests.Session()
    cookie = get_secret()

    token = get_synchronizer_token(session)
    print(f"Synchronizer Token: {token}")
    
    reset_response = reset_search(session, token, cookie)
    if reset_response.status_code == 200:
        print("Reset successful")
        result = make_search_request(session, token, subject, course_num, cookie)
        parsed_courses = parse_course_data(result['data'])
        return parsed_courses
    else:
        print("Reset failed")

def parse_course_data(course_data):
    parsed_courses = []
    
    for course in course_data:
        # Construct the course title
        course_title = f"{course['subject']} {course['courseNumber']}"
        
        # Extract the sequence number
        sequence_number = course['sequenceNumber']
        
        # Extract the seat information
        seat_info = {
            'maximumEnrollment': course['maximumEnrollment'],
            'enrollment': course['enrollment'],
            'seatsAvailable': course['seatsAvailable'],
            'waitCapacity': course['waitCapacity'],
            'waitCount': course['waitCount'],
            'waitAvailable': course['waitAvailable'],
            'crossList': course['crossList'],
            'crossListCapacity': course['crossListCapacity'],
            'crossListCount': course['crossListCount'],
            'crossListAvailable': course['crossListAvailable']
        }
        
        # Combine the parsed data into a readable format
        parsed_course = {
            'courseTitle': course_title,
            'sequenceNumber': sequence_number,
            'seatInfo': seat_info
        }
        
        parsed_courses.append(parsed_course)
    
    return parsed_courses