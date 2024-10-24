import os
import re
import json
import time
from flask import Flask, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from assigments_urls import ASSIGNMENT_URLS

load_dotenv()

app = Flask(__name__)
CORS(app)

USERNAME = os.getenv("CODIO_USERNAME")
PASSWORD = os.getenv("CODIO_PASSWORD")

ASSIGNMENT_JSON_DIR = os.path.join(os.path.dirname(__file__), 'data', 'assignments')
REVIEWER_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'students_per_reviewer.json')


if not os.path.exists(ASSIGNMENT_JSON_DIR):
    os.makedirs(ASSIGNMENT_JSON_DIR)

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')


def login(driver):
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "(//input[@placeholder='Email or Username'])[1]"))
        ).send_keys(USERNAME)

        driver.find_element(By.XPATH, "(//input[@placeholder='Password'])[1]").send_keys(PASSWORD)

        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn--primary btn--large']"))
        ).click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='assignmentSmallList']"))
        )
        print("Login successful!")
    except Exception as e:
        print(f"Error during login: {e}")


def extract_grading_info(driver):
    try:
        modal_title_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='gradingModal-title'][1]"))
        )
        modal_title = modal_title_element.text.strip()
        modal_title = modal_title.replace("for ", "")
        if "'s " in modal_title:
            name, assignment_name = modal_title.split("'s ", 1)
        else:
            name = modal_title
            assignment_name = "Unknown assignment name"

        # Wait for the completed date element to be present and visible
        completed_date_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='gradingModal-completedDate'][1]"))
        )
        completed_date = completed_date_element.text.replace("Completed date: ", "").strip()

        project_url = None
        try:
            project_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Open Project')]"))
            )
            project_url = project_button.get_attribute('href')
        except:
            project_url = "No project URL"

        return {
            'name': name.strip(),
            'assignment_name': assignment_name.strip(),
            'completed_date': completed_date,
            'project_url': project_url
        }
    except Exception as e:
        print(f"Error extracting data from modal: {e}")
        return None


def process_assignment_url(url):
    """Process an individual assignment URL and save to a separate JSON file."""
    all_assignments = []

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        login(driver)
        time.sleep(5)

        empty_message = driver.find_elements(By.XPATH, "//span[@class='gradingQueue-emptyMessage']")
        if empty_message:
            print(f"No exercises in {url}. Skipping.")
            return []

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//span[@title='Open grading dialog']"))
        )

        grading_buttons = driver.find_elements(By.XPATH, "//span[@title='Open grading dialog']")
        for button in grading_buttons:
            button.click()
            time.sleep(2)

            grading_info = extract_grading_info(driver)
            if grading_info:
                all_assignments.append(grading_info)

            close_button = driver.find_element(By.XPATH, "(//i[normalize-space()='close'])[1]")
            close_button.click()
            time.sleep(1)

        if all_assignments:
            assignment_name = all_assignments[0]['assignment_name']
            safe_assignment_name = re.sub(r'[<>:"/\\|?*]', '_', assignment_name)
            assignment_file = os.path.join(ASSIGNMENT_JSON_DIR, f"{safe_assignment_name}.json")
            with open(assignment_file, 'w') as json_file:
                json.dump(all_assignments, json_file, indent=4)
            print(f"Saved data to {assignment_file}")

        return all_assignments
    except Exception as e:
        print(f"Error processing assignment at {url}: {e}")
        return []
    finally:
        driver.quit()


def scrape_assignments():
    all_assignments = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_assignment_url, url) for url in ASSIGNMENT_URLS]
        for future in futures:
            result = future.result()
            if result:
                all_assignments.extend(result)

    return all_assignments


@app.route('/scrape_assignments', methods=['GET'])
def scrape_assignments_route():
    try:
        data = scrape_assignments()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/show_assignments', methods=['GET'])
def show_assignments():
    try:
        all_assignments = []
        for filename in os.listdir(ASSIGNMENT_JSON_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(ASSIGNMENT_JSON_DIR, filename), 'r') as json_file:
                    data = json.load(json_file)
                    all_assignments.extend(data)
        return jsonify({"status": "success", "data": all_assignments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/exercises_per_reviewer/<reviewer_name>', methods=['GET'])
def exercises_per_reviewer(reviewer_name):
    try:
        # Load the reviewer to students mapping
        with open(REVIEWER_DATA_PATH, 'r') as reviewer_file:
            reviewer_data = json.load(reviewer_file)

        # Find the reviewer and their assigned students
        reviewer = next((r for r in reviewer_data if r["name"].lower() == reviewer_name.lower()), None)
        if not reviewer:
            return jsonify({"status": "error", "message": f"Reviewer {reviewer_name} not found."}), 404

        # Fetch assignments that match the students assigned to the reviewer
        all_assignments = []
        for filename in os.listdir(ASSIGNMENT_JSON_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(ASSIGNMENT_JSON_DIR, filename), 'r') as json_file:
                    assignment_data = json.load(json_file)
                    filtered_assignments = [
                        assignment for assignment in assignment_data if assignment['name'] in reviewer['students']
                    ]
                    all_assignments.extend(filtered_assignments)

        return jsonify({"status": "success", "data": all_assignments}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
