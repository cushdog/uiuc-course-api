import requests
import csv

def parse_teacher_data(raw_data):
    try:
        teacher_data = raw_data['data']['node']
        
        parsed_data = {
            'personal_info': {
                'first_name': teacher_data['firstName'],
                'last_name': teacher_data['lastName'],
                'department': teacher_data['department'],
                'id': teacher_data['id'],
                'legacy_id': teacher_data['legacyId']
            },
            'ratings': {
                'average_difficulty': teacher_data['avgDifficulty'],
                'average_rating': teacher_data['avgRating'],
                'would_take_again_percent': teacher_data['wouldTakeAgainPercent'],
                'number_of_ratings': teacher_data['numRatings']
            },
            'school': {
                'name': teacher_data['school']['name'],
                'city': teacher_data['school']['city'],
                'state': teacher_data['school']['state'],
                'country': teacher_data['school']['country']
            },
            'recent_ratings': []
        }
        
        for rating in teacher_data['ratings']['edges']:
            rating_data = rating['node']
            parsed_rating = {
                'id': rating_data['id'],
                'class': rating_data['class'],
                'date': rating_data['date'],
                'grade': rating_data['grade'],
                'comment': rating_data['comment'],
                'rating_tags': rating_data['ratingTags'].split('--'),
                'scores': {
                    'clarity': rating_data['clarityRating'],
                    'difficulty': rating_data['difficultyRating'],
                    'helpful': rating_data['helpfulRating']
                }
            }
            parsed_data['recent_ratings'].append(parsed_rating)
        
        return parsed_data
    except KeyError as e:
        print(f"Error parsing data: Key {e} not found")
        return None

def get_teacher_id(first_name, last_name):
    with open('data/CSVs/rmp_ids.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == first_name and row[1] == last_name:
                return row[2]
    return None

def fetch_teacher_info(id):

    url = "https://www.ratemyprofessors.com/graphql"

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Basic dGVzdDp0ZXN0",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://www.ratemyprofessors.com",
        "referer": "https://www.ratemyprofessors.com/professor/1633738",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # Extended GraphQL query to include ratings
    query = """
    query TeacherRatingsPageQuery($id: ID!) {
    node(id: $id) {
        ... on Teacher {
        id
        legacyId
        firstName
        lastName
        department
        school {
            name
            city
            state
            country
        }
        numRatings
        avgRating
        wouldTakeAgainPercent
        avgDifficulty
        ratings(first: 3) {
            edges {
            node {
                id
                class
                comment
                grade
                date
                helpfulRating
                clarityRating
                difficultyRating
                ratingTags
            }
            }
        }
        }
    }
    }
    """

    # The variables for the query
    variables = {
        "id": id
    }

    # Construct the payload
    payload = {
        "query": query,
        "variables": variables
    }

    # Send the POST request
    response = requests.post(url, json=payload, headers=headers)

    # Check the response
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)

def search_teacher(first_name, last_name):

    id = get_teacher_id(first_name, last_name)
    teacher_info = fetch_teacher_info(id)

    return parse_teacher_data(teacher_info)