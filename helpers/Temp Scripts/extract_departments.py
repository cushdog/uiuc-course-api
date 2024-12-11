import json

# Load the JSON data from professors.json
with open('professors.json', 'r') as file:
    data = json.load(file)

# Extract unique department names using a set
unique_departments = set()
for teacher in data.get('data', []):
    department_name = teacher.get('departmentname', 'Unknown Department')
    unique_departments.add(department_name)

# Write unique department names to departments.txt
with open('departments.txt', 'w') as output_file:
    for department in sorted(unique_departments):  # Sorting for consistent output
        output_file.write(department + '\n')

print(f"Unique department names have been written to departments.txt")
