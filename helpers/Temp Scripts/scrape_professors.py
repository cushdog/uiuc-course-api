import json
import re
from bs4 import BeautifulSoup

# Assuming 'html' variable contains the HTML content
# If you're fetching the webpage directly:
import requests
url = 'http://illinois.edu/ds/facultyListing'
response = requests.get(url)
html = response.content

soup = BeautifulSoup(html, 'html.parser')
retval = []

# Define a regular expression pattern to match class names with any amount of whitespace
pattern = re.compile(r'\bh2-sans\s+border-bottom\b')

# Find all h2 elements where the class attribute matches the pattern
colleges = soup.find_all('h2', class_=pattern)

for college in colleges:
    collegename = college.find('a').get_text(strip=True)
    print('Processing college:', collegename)
    # Now we need to get the departments under this college.

    # The departments are h3 elements with class 'list-expand-header' following the college h2,
    # until the next college h2 or until the end.

    nextNode = college.find_next_sibling()

    while nextNode and nextNode.name != 'h2':
        if nextNode.name == 'h3' and nextNode.get('class') and 'list-expand-header' in nextNode.get('class', []):
            # This is a department
            departmentname = nextNode.find_all('a')[-1].get_text(strip=True)
            print('  Processing department:', departmentname)
            # The next ul element contains the faculty list
            faculty_list = nextNode.find_next_sibling('ul', class_='place-off-screen')
            if faculty_list:
                for faculty in faculty_list.find_all('li'):
                    ret = {
                        'collegename': collegename,
                        'departmentname': departmentname,
                    }
                    # Extract faculty information
                    # Get the name
                    name = faculty.find('a').get_text(strip=True)
                    ret['name'] = name
                    # Get the link
                    link = faculty.find('a')['href']
                    ret['link'] = link
                    # Get email and netid from link
                    email_param = link.split('search=')[-1] if 'search=' in link else ''
                    email = email_param
                    ret['email'] = email
                    netid = email.split('@')[0] if '@' in email else ''
                    ret['netid'] = netid
                    # Split name into last name and first name and middle name
                    name_parts = name.split(',')
                    last_name = name_parts[0].strip()
                    first_middle = name_parts[1].strip() if len(name_parts) > 1 else ''
                    first_middle_parts = first_middle.split(' ')
                    first_name = first_middle_parts[0] if len(first_middle_parts) > 0 else ''
                    middle_name = ' '.join(first_middle_parts[1:]) if len(first_middle_parts) > 1 else ''
                    ret['firstname'] = first_name
                    ret['lastname'] = last_name
                    ret['middlename'] = middle_name
                    # Get role
                    role_span = faculty.find('span', class_='notes')
                    role = role_span.get_text(strip=True) if role_span else 'None Specified'
                    ret['role'] = role

                    retval.append(ret)
        # Move to the next sibling
        nextNode = nextNode.find_next_sibling()

# Now write the results to a JSON file
finalreturn = {'data': retval}
with open('professors.json', 'w') as outfile:
    json.dump(finalreturn, outfile, sort_keys=True, indent=4)
