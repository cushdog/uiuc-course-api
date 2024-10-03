import requests
import json
import csv


def search_teachers(school_id, search_text=""):
    url = "https://www.ratemyprofessors.com/graphql"
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Basic dGVzdDp0ZXN0",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://www.ratemyprofessors.com",
        "referer": f"https://www.ratemyprofessors.com/search/professors/{school_id}",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    query = """
    query TeacherSearchResultsPageQuery(
        $query: TeacherSearchQuery!
        $schoolID: ID
        $cursor: String
    ) {
        search: newSearch {
            teachers(query: $query, first: 20, after: $cursor) {
                didFallback
                edges {
                    cursor
                    node {
                        id
                        firstName
                        lastName
                        department
                        school {
                            name
                            id
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
                resultCount
            }
        }
        school: node(id: $schoolID) {
            ... on School {
                name
            }
        }
    }
    """

    variables = {
        "query": {
            "text": search_text,
            "schoolID": school_id,
            "fallback": True
        },
        "schoolID": school_id
    }

    payload = {
        "query": query,
        "variables": variables
    }

    all_teachers = []
    has_next_page = True
    cursor = None

    while has_next_page:
        if cursor:
            variables["cursor"] = cursor
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("GraphQL Errors:", data['errors'])
                break
            teachers = data['data']['search']['teachers']['edges']
            all_teachers.extend(teachers)
            
            page_info = data['data']['search']['teachers']['pageInfo']
            has_next_page = page_info['hasNextPage']
            cursor = page_info['endCursor']
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            break

    return all_teachers

def output_to_file(teachers, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for teacher in teachers:
            node = teacher['node']
            f.write(f"{node['firstName']}, {node['lastName']} - {node['id']} - {node['department']}\n")

def download_teacher_ratings(school_id="U2Nob29sLTExMTI="):

    search_text = ""

    teachers = search_teachers(school_id, search_text)
    if teachers:
        output_to_file(teachers, "teachers_output.txt")
        print(f"Found {len(teachers)} teachers. Results written to teachers_output.txt")
    else:
        print("No teachers found or an error occurred.")

def fix_teacher_output():

    # Open the input text file in read mode
    with open('teachers_output.txt', 'r') as file:
        lines = file.readlines()

    # Open the output CSV file in write mode
    with open('output.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write the header row to the CSV file
        csvwriter.writerow(['name', 'surname', 'id'])
        
        # Process each line from the input file
        for line in lines:
            # Split the line based on hyphen ('-')
            parts = line.strip().split(' - ')
            
            # Extract the name and ID parts
            name_part = parts[0].split(', ')
            first_name = name_part[0]
            last_name = name_part[1]
            user_id = parts[1]
            
            # Write the row to the CSV file
            csvwriter.writerow([first_name, last_name, user_id])

        print("CSV file created successfully!")

def get_id(first_name="Geoffrey", last_name="Herman"):
    with open('data/CSVs/rmp_ids.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == first_name and row[1] == last_name:
                return row[2]
    return None

def main():

    id = "VGVhY2hlci0xNzk5MDMw"
    fetch_teacher_info(get_id())

if __name__ == "__main__":
    main()