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
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
CORS(app)


USERNAME = os.getenv("CODIO_USERNAME")
PASSWORD = os.getenv("CODIO_PASSWORD")

ASSIGNMENT_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'assignments_data.json')
REVIEWER_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'students_per_reviewer.json')

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')


def scroll_to_element(element, driver):
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(2)


def scroll_to_bottom(driver):
    """Scrolls to the bottom of the page to ensure all elements are loaded."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def dismiss_cookie_consent(driver):
    """Dismiss the cookie consent if the 'Got it' button appears on the page."""
    try:
        # Locate the "Got it" button by its text
        got_it_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Got it')]"))
        )
        got_it_button.click()  # Click the "Got it" button
        print("Cookie consent 'Got it' button clicked.")
        time.sleep(2)  # Wait to ensure the button is dismissed
    except TimeoutException:
        print("No 'Got it' button found.")
    except Exception as e:
        print(f"Error dismissing 'Got it' button: {e}")


def login(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "(//input[@placeholder='Email or Username'])[1]"))
        ).send_keys(USERNAME)

        driver.find_element(By.XPATH, "(//input[@placeholder='Password'])[1]").send_keys(PASSWORD)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn--primary btn--large']"))
        ).click()


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='assignmentSmallList']"))
        )
        print("Login successful!")
    except Exception as e:
        print(f"Error during login: {e}")


def extract_grading_info(driver):
    try:
        modal_title = driver.find_element(By.XPATH, "//div[@class='gradingModal-title'][1]").text.strip()
        modal_title = modal_title.replace("for ", "")
        if "'s " in modal_title:
            name, assignment_name = modal_title.split("'s ", 1)
        else:
            name = modal_title
            assignment_name = "Unknown assignment name"

        completed_date = driver.find_element(By.XPATH, "//div[@class='gradingModal-completedDate'][1]").text
        completed_date = completed_date.replace("Completed date: ", "").strip()

        project_url = None
        try:
            project_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Open Project')]")
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


def scrape_assignments():
    all_assignments = []
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        grading_queue_url = "https://codio.com/home/teacher/f6c6db9ebaca19737656cab4fe8cf722/grading-queue?assignmentId=0803f2e479409d35e5b3e11bdc4ff0aa"
        driver.get(grading_queue_url)

        login(driver)
        time.sleep(10)
        dismiss_cookie_consent(driver)

        while True:
            try:
                assignment_elements = driver.find_elements(By.XPATH,
                                                           "//tr[contains(@class,'assignmentSmallList-row')]//td[contains(@class,'assignmentSmallList-name')]")
                print(f"Found {len(assignment_elements)} assignments.")
                break
            except StaleElementReferenceException:
                print("Stale element found. Refetching assignment elements...")
                time.sleep(2)
                continue

        # Process each assignment element
        for index in range(len(assignment_elements)):
            try:
                assignment_elements = driver.find_elements(By.XPATH,
                                                           "//tr[contains(@class,'assignmentSmallList-row')]//td[contains(@class,'assignmentSmallList-name')]")
                assignment_element = assignment_elements[index]
                scroll_to_element(assignment_element, driver)  # Ensure element is visible before interaction
                assignment_element.click()
                time.sleep(2)

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@title='Open grading dialog']"))
                )

                grading_buttons = driver.find_elements(By.XPATH, "//span[@title='Open grading dialog']")
                for button in grading_buttons:
                    scroll_to_element(button, driver)
                    button.click()
                    time.sleep(2)

                    grading_info = extract_grading_info(driver)
                    if grading_info:
                        all_assignments.append(grading_info)

                    close_button = driver.find_element(By.XPATH, "(//i[normalize-space()='close'])[1]")
                    close_button.click()
                    time.sleep(1)

                driver.back()
                time.sleep(2)

                # Scroll down after each interaction to ensure more elements are loaded
                scroll_to_bottom(driver)

            except Exception as e:
                print(f"Error processing assignment {index + 1}: {e}")
                continue

        # Save the scraped data
        with open(ASSIGNMENT_DATA_PATH, 'w') as json_file:
            json.dump(all_assignments, json_file, indent=4)

        return all_assignments
    finally:
        driver.quit()


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
        with open(ASSIGNMENT_DATA_PATH, 'r') as json_file:
            data = json.load(json_file)
        return jsonify({"status": "success", "data": data}), 200
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "No assignment data found. Please run the scraper first."}), 404


@app.route('/exercises_per_reviewer/<reviewer_name>', methods=['GET'])
def exercises_per_reviewer(reviewer_name):
    try:
        with open(REVIEWER_DATA_PATH, 'r') as reviewer_file:
            reviewer_data = json.load(reviewer_file)

        reviewer = next((r for r in reviewer_data if r["name"].lower() == reviewer_name.lower()), None)
        if not reviewer:
            return jsonify({"status": "error", "message": f"Reviewer {reviewer_name} not found."}), 404

        with open(ASSIGNMENT_DATA_PATH, 'r') as assignments_file:
            assignments_data = json.load(assignments_file)

        filtered_assignments = [assignment for assignment in assignments_data if assignment['name'] in reviewer['students']]

        return jsonify({"status": "success", "data": filtered_assignments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
