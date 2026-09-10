# Code Review for Yuuqq/dianping_textmining

This document contains a thorough code review of the `dianping_textmining` repository, focusing on architecture, security, reliability, test coverage, and developer experience.

## CRITICAL

- **Hardcoded Cookie with Sensitive Information**
  - **File:** `大众点评爬虫/main.py` (Line 21)
  - **Impact:** The `cookie` string contains the highly sensitive `dper` token, which allows full session hijacking, and PII in the `ua` field (exposing a real username). (Note: While timestamped 2018-07, exposing session identifiers like this is a critical risk).
  - **Fix Suggestion:** Store cookies and other sensitive tokens in an external `.env` file that is ignored by Git, and load them using a library like `python-dotenv`.

- **Destructive Database Table Creation (`DROP TABLE`)**
  - **File:** `大众点评爬虫/mysqls.py` (Line 16)
  - **Impact:** `creat_table()` explicitly calls `DROP TABLE IF EXISTS DZDP`. Running this script re-creates the table and permanently deletes all previously scraped data. Additionally, the table has no primary key, meaning re-running scripts will result in duplicated entries.
  - **Fix Suggestion:** Remove the `DROP TABLE` statement and add an `id INT AUTO_INCREMENT PRIMARY KEY` to the schema.

- **Committed Resumption State File Breaking Default Run**
  - **File:** `大众点评爬虫/xuchuan.txt` (Lines 1-53)
  - **Impact:** The repository includes a populated `xuchuan.txt` file storing state up to page 53. Because the default function `craw_comment()` runs up to page 53, anyone cloning and running this project will simply do nothing (`range(54, 54)`), breaking the out-of-the-box experience entirely.
  - **Fix Suggestion:** Remove `xuchuan.txt` from the repository and add it to `.gitignore`.

- **Missing Transaction Rollback on Database Errors**
  - **File:** `大众点评爬虫/mysqls.py` (Line 42-46)
  - **Impact:** If `save_data` fails, it catches the error but doesn't call `db.rollback()`. This will cause the current transaction to remain aborted, meaning all subsequent inserts using this connection will continuously fail.
  - **Fix Suggestion:** Add `db.rollback()` within the `except` block.

- **PyMySQL 1.0 Positional Arguments Compatibility**
  - **File:** `大众点评爬虫/mysqls.py` (Line 11)
  - **Impact:** The `pymysql.connect("localhost","root","","TESTDB")` syntax uses positional arguments that were removed in PyMySQL 1.0. Modern installations will fail to connect.
  - **Fix Suggestion:** Use keyword arguments: `pymysql.connect(host="localhost", user="root", password="", database="TESTDB")`.

- **Privacy and Licensing Issues**
  - **File:** `文本分析挖掘/data.csv` and `文本分析挖掘/msyh.ttc`
  - **Impact:** `data.csv` contains roughly 32,000 real usernames and reviews, posing a PII risk. The 23MB font file `msyh.ttc` (Microsoft YaHei) is copyrighted and cannot be freely distributed.
  - **Fix Suggestion:** Remove these files from the repository entirely.

## HIGH

- **Hardcoded Database Credentials (Localhost)**
  - **File:** `大众点评爬虫/mysqls.py` (Line 11)
  - **Impact:** The code connects to MySQL using a hardcoded root user with an empty password. While dangerous, its impact is mitigated by connecting strictly to `localhost`.
  - **Fix Suggestion:** Use environment variables or a configuration file to store database credentials (e.g., `os.environ.get('DB_PASS')`).

- **Naked Except Clauses (Silent Failures)**
  - **File:** `大众点评爬虫/main.py` (Lines 50, 72, 80, 111) and `大众点评爬虫/mysqls.py` (Line 45)
  - **Impact:** Using `except:` without specifying an exception class catches all exceptions, including `KeyboardInterrupt` and `SystemExit`. It also silently ignores network errors, database errors, and logical bugs, making debugging extremely difficult. (Note: `except re.error` on line 58 is a valid Python 2/3 fallback for emojis, not a naked except).
  - **Fix Suggestion:** Catch specific exceptions like `Exception` or `pymysql.Error`. Log the error messages using the `logging` module instead of just printing "产生异常" or "跳过本次".

- **Side Effects on Import**
  - **File:** `大众点评爬虫/mysqls.py` (Lines 11-12)
  - **Impact:** `db = pymysql.connect(...)` is executed at the module level. Simply importing this module will attempt to connect to the database. This makes unit testing very hard and can crash scripts that import the module without an active database running.
  - **Fix Suggestion:** Encapsulate the database connection logic inside a class or a function (e.g., `get_db_connection()`), or use a context manager to handle the connection lifecycle.

## MEDIUM

- **State Management Bug in Resuming Capability**
  - **File:** `大众点评爬虫/main.py` (Lines 116-123)
  - **Impact:** The resume functionality just reads the last line of `xuchuan.txt` to get the page number, without indicating which `shopID` it belongs to. If the script is stopped on shop A and restarted on shop B, it will skip pages for shop B.
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