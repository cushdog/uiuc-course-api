import requests

# Define the URL
url = "https://www.ratemyprofessors.com/professor/831224"

# Define the headers
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
}

# Define the cookies
cookies = {
    "logglytrackingsession": "1750d6f9-667c-4ac5-8add-d41df65d4ff9",
    "trc_cookie_storage": "taboola%2520global%253Auser-id%3D971e3204-dec3-4185-981e-13436406680f-tuctdfdfcdc",
    "FCNEC": "%5B%5B%22AKsRol-ryXR4ayI8CwPK3CI1UHHRWHYA4KYP2beYJyByX7PF3PN1iyEJsJonOTkGfJyydUAB4TdmB2iHaW_4_4oFu4D7MxZJ9BnGLD_EDG8DERGKnxVlNtD7zv_6Yxp635ekvY7XVeQzym6qsGVCZZ9ZASgrHLAsjQ%3D%3D%22%5D%5D",
    "cto_bundle": "224No19hc2poNXMxa2Jxb2xYN3dodTdrNldxeXZhMWFMajdvUEFUbGtvWHJkMENPTFk2dmJ4bm1nUU81SnNUYXpDa29rQSUyQk1RSkIyVExQR3pITDhoSWFPbEdaS1VyaTIzVEFLaVRlNXN3NjloUWQycnV3TVF1ZmhqNnJsU0slMkZ2NmlKTyUyQg",
    "_ga": "GA1.2.2002739692.1728345948",
    "_gid": "GA1.2.428155709.1728345948",
    "_au_1d": "AU1D-0100-001728345948-8Z37T8FY-AD3D",
    "_hjSessionUser_1667000": "eyJpZCI6ImY4Njg2ZGM4LTkyYWEtNWJmMS1hNTcyLWE3YWM3Zjg1MDgxNyIsImNyZWF0ZWQiOjE3MjgzNDU5NDgxNDQsImV4aXN0aW5nIjp0cnVlfQ==",
    # Add the rest of the cookies similarly
}

# Make the request
response = requests.get(url, headers=headers, cookies=cookies)

# Print the status code and content of the response
print(f"Status code: {response.status_code}")
print(response.text)
