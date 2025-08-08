=====
Usage
=====


Options
=======

These are the options that can be added to the ``pytest.ini`` file.

----

* ``extras_screenshots``

The screenshots to add in the report.

Accepted values:

* ``all``: Include all gathered screenshots in the report.

* ``last``: Include only the last screenshot of each test in the report. Works only when using **pytest-html** plugin and if the API has been previously called during the test execution.

* ``fail``: Include only the last screenshot of each failed and skipped test in the report. Works only when using **pytest-html** plugin and if the API has been previously called during the test execution.

* ``none``: Exclude all screenshots in the report.

Default value: ``all``

----

* ``extras_sources``

Whether to include gathered webpage sources in the report.

Default value: ``False``

----

* ``extras_attachment_indent``

The indent to use for attachments.

Accepted values: any positive integer.

Default value: ``4``

----

* ``extras_issue_link_pattern``

The pattern for the issues links (example: https://bugtracker.com/issues/{})

Default value: ``None``

----

* ``extras_tms_link_pattern``

The pattern for the test-case links (example: https://tms.com/tests/{})

Default value: ``None``

----

* ``extras_links_column``

The type of links to display in the **Links** columns of the pytest report.

Accepted values: ``all``, ``issue``, ``tms``, ``link`` or ``none``

Default value: ``all``

----

* ``extras_title``

The test report title

Default value: ``Test Report``


API
===

The function scoped fixture ``report`` provides the following methods:

To add a step with screenshot:

.. code-block:: python

  screenshot(
      comment: str,                                # Comment of the test step.
      target: WebDriver | WebElement | Page | Locator = None,  # The screenshot target.
      full_page: bool = True,                      # Whether to take a full page screenshot.
      page_source: bool = False,                   # Whether to include the webpage HTML source.
      escape_html: bool = True                     # Whether to escape HTML characters in the comment.
  )

To add a step with attachment:

.. code-block:: python

  attach(
      comment: str,                                 # Comment of the test step.
      body: str | bytes | dict | list[str] = None,  # The content/body of the attachment.
      source: str = None,                           # The filepath of the attachment.
      mime: Mime | str = None,                      # The attachment mime type.
      escape_html: bool = True                      # Whether to escape HTML characters in the comment.
  )

  # Type of 'body'' parameter:
  #    str: - for XML, JSON, YAML, CSV or TXT attachments
  #         - for image attachments if it is a base64 string
  #    bytes: for image attachments
  #    dict: for JSON attachments
  #    list[str]: for list-uri attachments

  # The supported mime types are:
  #    report.Mime.JSON   or "application/json"   or "json"
  #    report.Mime.XML    or "application/xml"    or "xml"
  #    report.Mime.YAML   or "application/yaml"   or "yaml"
  #    report.Mime.MP3    or "audio/mpeg"         or "mp3"
  #    report.Mime.OGA    or "audio/ogg"          or "oga"
  #    report.Mime.BMP    or "image/bmp"          or "bmp"
  #    report.Mime.GIF    or "image/gif"          or "gif"
  #    report.Mime.JPEG   or "image/jpeg"         or "jpeg"
  #    report.Mime.PNG    or "image/png"          or "png"
  #    report.Mime.SVG    or "image/svg+xml"      or "svg"
  #    report.Mime.CSV    or "text/csv"           or "csv"
  #    report.Mime.HTML   or "text/html"          or "html"
  #    report.Mime.TEXT   or "text/plain"         or "text"
  #    report.Mime.URI    or "text/uri-list"      or "uri"
  #    report.Mime.MP4    or "video/mp4"          or "mp4"
  #    report.Mime.OGV    or "video/ogg"          or "ogv"
  #    report.Mime.WEBM   or "video/webm"         or "webm"


To add links to the report:

.. code-block:: python

  @pytest.mark.issue("<issue keys separated by comma>", icon: str)
  @pytest.mark.tms("<test-case keys separated by comma>", icon: str)
  @pytest.mark.link(url: str, name: str, icon: str)


Limitations
===========

* Limited support for the ``--self-contained-html`` option of the **pytest-html** plugin. The report still contains links for attachments of unsopported mime types.

* No support for any kind of parallel tests execution (multi-treads, multi-tabs or multi-windows).

* For Playwright, only **sync_api** is supported.

* When using **Allure** with **pytest-bdd**, the **allure-pytest** plugin should be installed instead of **allure-pytest-bdd**.


Examples
========

When using the **pytest-html** plugin (with the ``--html`` option), an external CSS file may be provided with the ``--css`` option.


Command-line invocation
-----------------------

If using pytest-html report:

.. code-block:: bash

  pytest --html=path/to/report --css=path/to/css

If using Allure report:

.. code-block:: bash

  pytest --alluredir=path/to/allure-results

If using both reports:

.. code-block:: bash

  pytest --html=path/to/report --css=path/to/css --alluredir=path/to/allure-results


Sample ``pytest.ini`` file
--------------------------

.. code-block:: ini

  extras_attachment_indent = 4
  extras_screenshots = all
  extras_sources = False
  extras_issue_link_pattern = http://bugtracker.com/{}
  extras_tms_link_pattern = http://tms.com/tests/{}
  extras_links_column = all
  extras_title = My awesome test report


Sample code
-----------

* Example with Selenium

.. code-block:: python

  def test_with_selenium(report):
      """
      This is a test using Selenium
      """
      driver = WebDriver()
      driver.get("https://www.selenium.dev/selenium/web/web-form.html")
      report.screenshot("Get the webpage to test", driver)
      driver.find_element(By.ID, "my-text-id").send_keys("Hello World!")
      report.screenshot("<h1>Set input text</h1>", driver, full_page=True, escape_html=False)
      driver.find_element(By.NAME, "my-password").send_keys("password")
      report.screenshot(comment="Another comment", target=driver)
      report.screenshot("Comment without screenshot")
      report.screenshot(comment="Comment without screenshot")
      driver.quit()


* Example with Playwright

.. code-block:: python

  def test_with_playwright(browser: Browser, report):
      """
      This is a test using Playwright
      """
      context = browser.new_context(record_video_dir="path/to/videos/")
      page = context.new_page()
      page.goto("https://www.wikipedia.org")
      report.screenshot("Wikipedia page", page)
      context.close()
      page.close()
      report.attach("Recorded video", source=page.video.path(), report.Mime.WEBM)


* Example with attachments

.. code-block:: python

  def test_attachments(report):
      report.attach(
          "This is a XML document:",
          body="<root><child>text</child></root>",
          mime=report.Mime.XML
      )
      report.attach(
          comment="This is a JSON document:",
          source="path/to/file",
          mime="json"
      )


* Example with links

.. code-block:: python

  @pytest.mark.tms("TEST-3")
  @pytest.mark.issue("PROJ-123, PROJ-456")
  @pytest.mark.link("https://example.com")
  @pytest.mark.link(uri="https://wikipedia.org", name="Wikipedia")
  @pytest.mark.link(uri="https://wikipedia.org", name="Wikipedia", icon="&#129373;")
  def test_link_markers(report)
      pass


* Example with pytest-bdd (cucumber)

.. code-block:: text

  Feature: Wikipedia

  Scenario: Search in Wikipedia
    Given I go to Wikipedia
    When I search for "pizza"
    Then the page title is "Pizza - Wikipedia"


.. code-block:: python

  import pytest
  from pytest_bdd import scenarios, given, when, then, parsers
  from playwright.sync_api import sync_playwright, Page
  
  scenarios('features/wikipedia.feature')
  
  @pytest.fixture
  def playwright_context():
      with sync_playwright() as p:
          browser = p.chromium.launch(headless=True)
          page = browser.new_page()
          yield page
          browser.close()
  
  @given('I go to Wikipedia')
  def go_to_wikipedia(playwright_context: Page, report):
      playwright_context.goto("https://www.wikipedia.org")
      assert "Wikipedia" in playwright_context.title()
      report.screenshot("Wikipedia page", playwright_context)
  
  @when(parsers.parse('I search for "{term}"'))
  def search_wikipedia(playwright_context: Page, term, report):
      playwright_context.locator("[id='searchInput']").fill(term)
      playwright_context.keyboard.press("Enter")
      playwright_context.wait_for_load_state("load")
      report.screenshot("The searched page", playwright_context)
  
  @then(parsers.parse('the page title is "{title}"'))
  def check_title(playwright_context: Page, title):
      assert playwright_context.title() == title


Sample CSS file
===============

.. code-block:: css

  .extras_comment {
      font-family: monospace;
      color: blue;
  }
  
  .extras_comment strong {
      color: black;
  }
  
  .extras_color_skipped {
      color: #727272;
  }
  
  .extras_color_xfailed,
  .extras_color_xpassed {
      color: #b37400;
  }
  
  .extras_color_error {
      color: black;
  }
  
  .extras_color_failed {
      color: red;
  }
  
  .extras_header td {
      padding-top: 10px;
      vertical-align: top;
  }
  
  .extras_header_separator {
      width: 10px;
  }
  
  .extras_td_multimedia {
      width: 320px;
  }
  
  .extras_td_multimedia div {
      text-align: center;
  }
  
  .extras_title {
      color: black;
      font-size: medium;
      font-weight: bold;
  }
  
  .extras_description {
      color: black;
      font-size: 16px;
  }
  
  .extras_params_key {
      color: #999;
      font-size: 14px;
  }
  
  .extras_params_value {
      color: black;
      font-size: 14px;
  }
  
  .extras_header_block {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      margin-top: 0px;
      margin-bottom: 0px;
      margin-left: 0px;
  }

  .visibility_links a {
      text-decoration: none;
      color: darkslategrey;
  }
  
  .extras_separator {
      height: 1px;
      background-color: gray;
  }
  
  .extras_video {
      border: 1px solid #e6e6e6;
      width: 300px;
      height: 170px;
  }
  
  .extras_td_multimedia svg {
      border: 1px solid #e6e6e6;
      width: 300px;
      height: 170px;
  }
  
  .extras_image {
      border: 1px solid #e6e6e6;
      width: 300px;
      height: 170px;
      object-fit: cover;
      object-position: top;
  }
  
  .extras_page_src {
      color: #00b5ff;
      font-size: 12px;
  }
  
  .extras_attachment {
      color: black;
      margin-left: 30px;
      margin-right: 30px;
  }
  
  .extras_comment code,
  .extras_attachment_block {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      padding: .2em .4em;
      color: black;
      background-color: #818b981f;
      border-radius: 6px;
  }
  
  .extras_attachment_error {
      color: red;
  }
  
  .extras_iframe {
      margin-top: 15px;
      margin-left: 30px;
      margin-right: 30px;
      resize: both;
      overflow: auto;
      background-color: #faf0e6;
      inline-size: -webkit-fill-available;
  }
  
  .extras_status {
      border-radius: 3px;
      color: #fff;
      font-size: medium;
      font-weight: bold;
      letter-spacing: 1px;
      padding: 2px 4px 2px 5px;
      vertical-align: baseline;
  }
  
  .extras_status_passed {
      background: #97cc64;
  }
  
  .extras_status_failed {
      background: #fd5a3e;
  }
  
  .extras_status_skipped {
      background: #aaa;
  }
  
  .extras_status_xfailed,
  .extras_status_xpassed {
      background: orange;
  }
  
  .extras_status_error {
      background: black;
  }
  
  .extras_status_reason {
      color: black;
      font-size: 14px;
  }


Sample reports
==============

* pytest-html sample report

.. image:: demo-pytest.png

* Allure sample report

.. image:: demo-allure.png
