from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import pickle


class HackerrankSession:
    flag = True

    def __init__(self, username, password):
        print("4")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")   # enable later if needed
        self.__driver = webdriver.Chrome(options=chrome_options)

        print("HELLO its working")
        self.__driver.get('https://www.hackerrank.com/auth/login')

        m = self.__driver.find_element("name", "username")
        m.send_keys(username)
        m = self.__driver.find_element("name", "password")
        m.send_keys(password)
        print("1")

        login_button = self.__driver.find_element(
            By.XPATH, "//button[contains(@class, 'c-cUYkx') and text()='Log In']")
        ActionChains(self.__driver).move_to_element(login_button).click(login_button).perform()

        cookies = self.__driver.get_cookies()
        with open("cookies.pkl", "wb") as cookie_file:
            pickle.dump(cookies, cookie_file)

    def fetch_link(self, link):
        if not link.startswith("http"):
            link = f"https://www.hackerrank.com/{link[1:] if link.startswith('/') else link}"
        self.__driver.get(link)
        time.sleep(3)

    def check_page_valid(self, page, url):
        url = url + f"/{page}"
        self.fetch_link(url)
        try:
            self.__driver.find_element("css selector", "div.pagination > ul > li.active")
        except:
            self.flag = False
        return True

    def fetch_users(self, contest_slug):
        page = 1
        contest_submission_url = f"contests/{contest_slug}/leaderboard"

        with open("cookies.pkl", "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
            for cookie in cookies:
                self.__driver.add_cookie(cookie)

        self.__driver.refresh()
        usernames = []

        while self.check_page_valid(page, contest_submission_url):
            rows = self.__driver.find_elements("class name", "leaderboard-row")
            for submission_item in rows:
                divs = submission_item.find_elements("tag name", "div")
                if len(divs) > 1:
                    username = divs[1].find_element("tag name", "a").get_attribute('href')
                    username = username.split("/")[-1]
                    print(username)
                    usernames.append(username)

            if not self.flag:
                break
            page += 1

        return usernames

    @property
    def driver(self):
        return self.__driver


class UserContestSubmissions:

    def __init__(self, username, contest_slug, hr_session):
        self.contest_slug = contest_slug
        self.username = username
        self.hr_session = hr_session

    def __safe_float(self, val):
        try:
            return float(val)
        except:
            return 0.0

    def __safe_int(self, val):
        try:
            return int(val)
        except:
            return 0

    def __fetch_code(self, src_link):
        self.hr_session.fetch_link(src_link)
        code_elements = self.hr_session.driver.find_elements("class name", "CodeMirror-line")
        return "\n".join([line.text for line in code_elements])

    def __parse_submission_row(self, submission_item):
        headers = ['problem_slug', 'username', 'id', 'language', 'time',
                   'result', 'score', 'status', 'during_contest', 'srclink']
        not_required = ['status', 'during_contest']
        cols = {}

        columns = submission_item.find_elements("tag name", "div")
        limit = min(len(columns), len(headers))

        for i in range(limit):
            column = columns[i]
            val = ""

            try:
                val = column.find_element("tag name", "a").get_attribute('href')
                if i < len(headers) - 1:
                    val = val.split("/")[-1]
            except:
                try:
                    val = column.find_element("tag name", "p").text.strip()
                except:
                    val = ""

            if headers[i] == "score":
                val = self.__safe_float(val)
            elif headers[i] == "time":
                val = self.__safe_int(val)

            if headers[i] not in not_required:
                cols[headers[i]] = val

        # guarantee keys exist
        cols.setdefault("score", 0.0)
        cols.setdefault("time", 0)

        return cols

    def __fetch_latest_user_attempts(self, user_attempts, last_fetch_time):
        current_item_time = last_fetch_time
        print("h1")

        items = self.hr_session.driver.find_elements("class name", "submissions_item")
        for submission_item in items:
            print("h2")

            cols = self.__parse_submission_row(submission_item)

            current_item_time = self.__safe_int(cols.get("time", 0))
            problem_slug = cols.get("problem_slug", "")

            if not problem_slug:
                continue

            if problem_slug in user_attempts:
                prev_score = self.__safe_float(user_attempts[problem_slug].get("score", 0))
                current_score = self.__safe_float(cols.get("score", 0))

                if prev_score < current_score or (
                        prev_score == current_score and last_fetch_time < current_item_time):
                    cols["insert"] = user_attempts[problem_slug].get("insert", False)
                    user_attempts[problem_slug] = cols
            else:
                cols["insert"] = True
                user_attempts[problem_slug] = cols

            if current_item_time <= last_fetch_time:
                break

        return current_item_time

    def fetch_latest_submissions(self, user_attempts, last_fetch_time):
        page = 1
        contest_submission_url = f"contests/{self.contest_slug}/judge/submissions/team/{self.username}"

        while self.hr_session.check_page_valid(page, contest_submission_url):
            time.sleep(5)
            time_processed = self.__fetch_latest_user_attempts(user_attempts, last_fetch_time)

            if time_processed <= last_fetch_time or not self.hr_session.flag:
                break
            page += 1

        final_attempts = {k: user_attempts[k] for k in user_attempts if isinstance(user_attempts[k], dict)}

        for problem_slug, attempt in final_attempts.items():
            if not attempt.get("source_code") and attempt.get("srclink"):
                attempt["source_code"] = self.__fetch_code(attempt["srclink"])

        return final_attempts

"""
Above is test code.
Actually we want:
for each contest to be web scraped:
  for each user in our list:
    update the contest submissions

# do plagiarism check for new submissions, i.e. submissions made during this session of scraping only

{'python-loops': {'problem_slug': 'python-loops', 'username': '20PA1A0412', 'id': '1333834691', 'language': 
'python3', 'time': 1976, 'result': 'Accepted', 'score': 10.0, 'srclink': 'https://www.hackerrank.com/contest
s/test-contest00/challenges/python-loops/submissions/code/1333834691', 'source_code': ''}, 

'write-a-function
': {'problem_slug': 'write-a-function', 'username': '20PA1A0412', 'id': '1333833709', 'language': 'python3',
 'time': 1955, 'result': 'Accepted', 'score': 10.0, 'srclink': 'https://www.hackerrank.com/contests/test-con
test00/challenges/write-a-function/submissions/code/1333833709', 'source_code': ''}}

"""
