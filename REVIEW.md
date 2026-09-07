# Code Review for Yuuqq/dianping_textmining

This document contains a thorough code review of the `dianping_textmining` repository, focusing on architecture, security, reliability, test coverage, and developer experience.

## CRITICAL

- **Hardcoded Database Credentials**
  - **File:** `大众点评爬虫/mysqls.py` (Line 11)
  - **Impact:** The code connects to MySQL using `pymysql.connect("localhost","root","","TESTDB")`. Hardcoding a root user with an empty password is a severe security risk if deployed or run in any shared environment.
  - **Fix Suggestion:** Use environment variables or a configuration file to store database credentials (e.g., `os.environ.get('DB_PASS')`).

- **Hardcoded Cookie with Sensitive Information**
  - **File:** `大众点评爬虫/main.py` (Line 17)
  - **Impact:** The `cookie` string contains session identifiers (`_lxsdk_s`, `_hc.v`, etc.). If these cookies are valid, exposing them in a public repository allows session hijacking and potential impersonation of the logged-in user.
  - **Fix Suggestion:** Store cookies and other sensitive tokens in an external `.env` file that is ignored by Git, and load them using a library like `python-dotenv`.

## HIGH

- **Naked Except Clauses (Silent Failures)**
  - **File:** `大众点评爬虫/main.py` (Lines 42, 53, 59, 78, 86) and `大众点评爬虫/mysqls.py` (Line 39)
  - **Impact:** Using `except:` without specifying an exception class catches all exceptions, including `KeyboardInterrupt` and `SystemExit`. It also silently ignores network errors, database errors, and logical bugs, making debugging extremely difficult.
  - **Fix Suggestion:** Catch specific exceptions like `requests.exceptions.RequestException` or `pymysql.Error`. Log the error messages using the `logging` module instead of just printing "产生异常" or "跳过本次".

- **Side Effects on Import**
  - **File:** `大众点评爬虫/mysqls.py` (Lines 11-12)
  - **Impact:** `db = pymysql.connect(...)` is executed at the module level. Simply importing this module will attempt to connect to the database. This makes unit testing very hard and can crash scripts that import the module without an active database running.
  - **Fix Suggestion:** Encapsulate the database connection logic inside a class or a function (e.g., `get_db_connection()`), or use a context manager to handle the connection lifecycle.

## MEDIUM

- **State Management Bug in Resuming Capability (xuchuan.txt)**
  - **File:** `大众点评爬虫/main.py` (Lines 80-83, 89-95)
  - **Impact:** The resume functionality (`xuchuan.txt`) just stores the page number without indicating which `shopID` it belongs to. If the script is stopped on shop A and restarted on shop B, it will skip pages for shop B. Additionally, writing to the same file dynamically can lead to partial reads or corruption.
  - **Fix Suggestion:** Use a structured format like JSON or SQLite to keep track of the crawl state per `shopID` (e.g., `{"521698": 53}`).

- **Missing Dependency Management and Setup Instructions**
  - **File:** Repository Root
  - **Impact:** There is no `requirements.txt`, `Pipfile`, or `environment.yml`. Developers have to guess which versions of `requests`, `bs4`, `fake_useragent`, `pymysql`, `jieba`, `sklearn`, and `pandas` to install, leading to "works on my machine" issues.
  - **Fix Suggestion:** Generate a `requirements.txt` listing all external dependencies with their specific versions.

- **Absence of Test Coverage**
  - **File:** Repository Root
  - **Impact:** There are no automated tests (`unittest` or `pytest`) for any of the scraping logic, parsing logic, or database operations. Regressions will likely go unnoticed during modifications.
  - **Fix Suggestion:** Add a `tests/` directory. Write unit tests for parsing functions like `parsePage` by providing mock HTML snippets, and use `responses` or `unittest.mock` to mock HTTP requests.

## LOW

- **Code Organization and Modularity**
  - **File:** `大众点评爬虫/main.py`
  - **Impact:** The code mixes scraping, HTML parsing, and database saving in the same file/functions. This tight coupling makes the code harder to maintain and test.
  - **Fix Suggestion:** Separate concerns: create one module for HTTP requests (Spider), one for parsing HTML (Parser), and one for database operations (Pipeline/DAO).

- **Improper Table Schema Data Type**
  - **File:** `大众点评爬虫/mysqls.py` (Line 20)
  - **Impact:** `cus_comment text(5000)` uses `text` with a length specifier, which is syntactically allowed in MySQL but often misleading or ignored, as `TEXT` is a variable-length string.
  - **Fix Suggestion:** Use `VARCHAR(5000)` if a strict limit is desired, or simply `TEXT` without the length modifier.

- **Lack of Docstrings and Type Hints**
  - **File:** Across Python files
  - **Impact:** Function arguments like `shopID` or `page` lack type hints, and many functions don't have docstrings explaining their inputs and outputs.
  - **Fix Suggestion:** Add Python type hints (`def craw_comment(shopID: str = '521698', page: int = 53) -> None:`) and standard docstrings for better developer experience.