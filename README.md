# UIUC Course API

A comprehensive API to retrieve and manage course-related data at the University of Illinois Urbana-Champaign.

## Version

1.0.0

## Server

- **URL:** [https://uiuc-course-api-production.up.railway.app](https://uiuc-course-api-production.up.railway.app)  
  **Description:** Local development server

---

## Endpoints

### `/prof-search`
**Method:** GET  
**Summary:** Search professors by name, semester, and year  
**Parameters:**
- **query** (string, required): Search query with format `last_name semester year`  

**Responses:**
- **200:** List of courses taught by the professor  
  - **Content-Type:** application/json  
  - **Schema:** Array of objects

---

### `/gpa-search`
**Method:** GET  
**Summary:** Search GPA information for a course  
**Parameters:**
- **query** (string, required): Search query with format `subject course_number`  

**Responses:**
- **200:** GPA data for the specified course  
  - **Content-Type:** application/json  
  - **Schema:** Object

---

### `/master-search`
**Method:** GET  
**Summary:** Retrieve subjects for a given semester and year  
**Parameters:**
- **query** (string, required): Search query with format `semester year`  

**Responses:**
- **200:** List of subjects  
  - **Content-Type:** application/json  
  - **Schema:** Array of strings

---

### `/interest-search`
**Method:** GET  
**Summary:** Retrieve areas of interest  
**Parameters:**
- **query** (string, required): Search query for areas of interest  

**Responses:**
- **200:** Matching interest data  
  - **Content-Type:** application/json  
  - **Schema:** Array of strings

---

### `/search`
**Method:** GET  
**Summary:** Search courses by subject and semester/year or specific course  
**Parameters:**
- **query** (string, required): Flexible query format to search by subject, course, semester, and year  

**Responses:**
- **200:** Course data  
  - **Content-Type:** application/json  
  - **Schema:** Object

---

### `/subject-info`
**Method:** GET  
**Summary:** Retrieve subject information as JSON  
**Parameters:**
- **subject** (string, required): Subject code (e.g., `CS`)  

**Responses:**
- **200:** Subject information in JSON  
  - **Content-Type:** application/json  
  - **Schema:** Object  
- **400:** Missing subject parameter  
- **500:** Error fetching or parsing data

---

### `/class-info`
**Method:** GET  
**Summary:** Retrieve class information  
**Parameters:**
- **class** (string, required): Class query with format `subject class_number`  

**Responses:**
- **200:** Class details  
  - **Content-Type:** application/json  
  - **Schema:** Object  
- **400:** Missing query parameter  
- **500:** Error fetching or parsing data

---

### `/gpa-distribution`
**Method:** GET  
**Summary:** Retrieve GPA distribution for a class  
**Parameters:**
- **class** (string, required): Class name with format `subject course_number`  

**Responses:**
- **200:** GPA distribution data  
  - **Content-Type:** application/json  
  - **Schema:** Object

---

### `/class-average-gpas`
**Method:** GET  
**Summary:** Retrieve average GPAs for a class  
**Parameters:**
- **subject** (string, required): Subject code  
- **course_number** (string, required): Course number  

**Responses:**
- **200:** Average GPA data  
  - **Content-Type:** application/json  
  - **Schema:** Array of objects  
    - **Properties:**
      - **class** (string)  
      - **average_gpa** (number)

---

### `/professor-stats`
**Method:** GET  
**Summary:** Retrieve professor statistics  
**Parameters:**
- **class** (string, required): Class name  

**Responses:**
- **200:** Professor statistics  
  - **Content-Type:** application/json  
  - **Schema:** Array of objects  
    - **Properties:**
      - **professor** (string)  
      - **average_gpa** (number)  
      - **total_students** (integer)