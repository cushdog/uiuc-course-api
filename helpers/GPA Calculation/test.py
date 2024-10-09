import pandas as pd
import re2
import math
import numpy as np

# Load data (update with actual CSV paths)
df = pd.read_csv("gpa.csv")
gen_ed = pd.read_csv("gen_ed.csv")
overall_gpa = pd.read_csv("overall_gpa.csv")

# Global constants and settings
FILTER_CATEGORIES = {
    'ACP': 'Advanced Composition', 'NW': 'Non-Western Cultures',
    'WCC': 'Western/Comparative Cultures', 'US': 'US Minority Cultures',
    'HP': 'Historical & Philosophical Perspectives', 'LA': 'Literature & the Arts',
    'LS': 'Life Sciences', 'PS': 'Physical Sciences', 'QR1': 'Quantitative Reasoning 1',
    'QR2': 'Quantitative Reasoning 2', 'BSC': 'Behavioral Sciences', 'SS': 'Social Sciences'
}
FILTERS = [{"checked": False, "value": str(idx), "text": value} for idx, value in enumerate(FILTER_CATEGORIES.values())]
SEM_FULL_FORM = {"sp": "Spring", "fa": "Fall", "su": "Summer", "wi": "Winter"}
WEIGHT = [4.00, 4.00, 3.67, 3.33, 3, 2.67, 2.33, 2, 1.67, 1.33, 1, 0.67, 0]

def get_grades(df):
    grades = [col for col in df.columns if len(col) < 3]
    return grades[:-1]  # Exclude 'W'

grades = get_grades(df)

def search_course(df, regex):
    regex = "(?i)(.+/|)" + regex.upper()
    all_courses = list(df["CourseFull"].unique())
    try:
        r = re2.compile(regex)
    except re2.error:
        return [], False
    shortlist = list(filter(r.match, all_courses))
    return shortlist, True

def apply_filters(filters_applied, course_list, df, gen_ed):
    gen_ed_df = gen_ed
    for filt in filters_applied:
        gen_ed_df = gen_ed_df[gen_ed_df[filt] == 1]
    valid_courses = list(gen_ed_df["Course"])
    course_df = df[(df["CourseFull"]).isin(course_list)]
    course_df = course_df[(course_df["Subject"] + " " + course_df["Number"].astype(str)).isin(valid_courses)]
    return list(course_df["CourseFull"].unique())

def get_avg_gpa(course_stats):
    gpasum = 0
    stdsum = 0
    numstudents = course_stats[grades].sum().sum()
    for ind, grade_sum in enumerate(course_stats[grades].sum()):
        gpasum += grade_sum * WEIGHT[ind]
    mean = gpasum / numstudents if numstudents else 0
    for ind, grade_sum in enumerate(course_stats[grades].sum()):
        stdsum += ((WEIGHT[ind] - mean) ** 2) * grade_sum
    std = math.sqrt(stdsum / numstudents) if numstudents else 0
    return mean, std

def get_prof_stats(course_stats):
    grade_prof_col = grades + ["Primary Instructor"]
    prof_stats_df = course_stats[grade_prof_col].groupby("Primary Instructor").sum()
    prof_stats = []

    for index, row in prof_stats_df.iterrows():
        num_students = row[grades].sum()
        gpas = []
        for ind, count in enumerate(row[grades]):
            gpas.extend([WEIGHT[ind]] * count)
        gpas = np.array(gpas)
        avg_gpa = gpas.mean() if len(gpas) > 0 else 0
        std_gpa = gpas.std() if len(gpas) > 0 else 0
        prof_stats.append(
            {
                "prof": index,
                "total": int(num_students),
                "avg": "%.3f" % float(avg_gpa),
                "std": "%.3f" % float(std_gpa)
            }
        )
    prof_stats = sorted(prof_stats, key=lambda k: k["avg"], reverse=True)
    return prof_stats

def perform_search(course_search_term, filters_applied):

    # Perform search
    course_list, success = search_course(df, course_search_term)
    if not success or len(course_list) == 0:
        print("No matching courses found")
    else:
        course_stats = apply_filters(filters_applied, course_list, df, gen_ed)
        if len(course_stats) > 0:
            # Limit to only the first course if multiple matches are found
            first_course = course_stats[0]
            course_stats_df = df[df["CourseFull"] == first_course]
            
            avg_gpa, std_gpa = get_avg_gpa(course_stats_df)
            prof_stats = get_prof_stats(course_stats_df)
            
            print(f"Course selected: {first_course}")
            avg_gpa = round(avg_gpa, 3)
            print(f"Average GPA: {avg_gpa:.3f}, Standard Deviation: {std_gpa:.3f}")
            print("Professor Stats:")
            for prof in prof_stats:
                print(f"  - {prof['prof']} | Total Students: {prof['total']} | Avg GPA: {prof['avg']} | Std Dev: {prof['std']}")

            return avg_gpa, prof_stats
        else:
            print("No matching courses found after applying filters")

# Test search, GPA calculation, and professor stats
course_search_term = "MATH 424"
filters_applied = []

perform_search(course_search_term, filters_applied)

