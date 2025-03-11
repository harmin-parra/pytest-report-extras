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

* ``last``: Include only the last screenshot of each test in the report. Works only if the API has been previously called during the test execution.

* ``fail``: Include only the last screenshot of each failed and skipped test in the report. Works only if the API has been previously called during the test execution.

* ``none``: Exclude all screenshots in the report.

Default value: ``all``

----

* ``extras_sources``

Whether to include gathered webpage sources in the report.

Default value: ``False``

----

* ``extras_description_tag``

The HTML tag for the test description (test docstring).

Accepted values: ``h1``, ``h2``, ``h3``, ``h4``, ``h5``, ``h6``, ``p`` or ``pre``

Default value: ``pre``

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


API
===

The function scoped fixture ``report`` provides the following methods:

To add a step with screenshot:

.. code-block:: python

  screenshot(
      comment: str,                                # Comment of the test step.
      target: WebDriver | WebElement | Page | Locator = None,  # The page or element.
      full_page: bool = True,                      # Whether to take a full page screenshot.
      page_source: bool = False,                   # Whether to include the webpage HTML source.
      escape_html: bool = False                    # Whether to escape HTML characters in the comment.
  )

To add a step with attachment:

.. code-block:: python

  attach(
      comment: str,                                 # Comment of the test step.
      body: str | bytes | dict | list[str] = None,  # The content/body of the attachment.
      source: str = None,                           # The filepath of the attachment.
      mime: str = None,                             # The attachment mime type.
      escape_html: bool = False                     # Whether to escape HTML characters in the comment.
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
  #    report.Mime.OGG    or "video/ogg"          or "ogg"
  #    report.Mime.OGV    or "video/ogv"          or "ogv"
  #    report.Mime.WEBM   or "video/webm"         or "webm"


To add links to the report:

.. code-block:: python

  @pytest.mark.issues("<issue keys separated by comma>")
  @pytest.mark.tms("<test-case keys separated by comma>")
  @pytest.mark.link(url="<url>", name="<name>")
  @pytest.mark.link(url="<url>")
  @pytest.mark.link("<url>", "<name>")
  @pytest.mark.link("<url>")


Limitations
===========

* Limited support for the ``--self-contained-html`` option of the **pytest-html** plugin. The report still contains links for attachments of unsopported mime types.

* No support for any kind of parallel tests execution (multi-treads, multi-tabs or multi-windows).

* For Playwright, only **sync_api** is supported.


Example
=======

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

  extras_description_tag = h1
  extras_attachment_indent = 4
  extras_screenshots = all
  extras_sources = False
  extras_issue_link_pattern = http://bugtracker.com/{}
  extras_tms_link_pattern = http://tms.com/tests/{}


Sample code
-----------

* Example adding Selenium screenshots

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


* Example adding Playwright screenshots

.. code-block:: python

  def test_with_playwright(page: Page, report):
      """
      This is a test using Playwright
      """
      page.goto("https://www.selenium.dev/selenium/web/web-form.html")
      report.screenshot("Get the webpage to test", page)
      report.screenshot(comment="Get the webpage to test", target=page, full_page=False)


* Example adding Playwright video

.. code-block:: python

  def test_with_playwright(browser: Browser, report):
      context = browser.new_context(record_video_dir="path/to/videos/")
      page = context.new_page()
      # Your test goes here
      context.close()
      page.close()
      report.attach("Recorded video", source=page.video.path(), mime="webm")


* Example adding attachments

.. code-block:: python

  def test_attachments(report):
      """
      This is a test adding XML & JSON attachments
      """
      report.attach(
          "This is a XML document:",
          body="<root><child>text</child></root>",
          mime=report.Mime.XML
      )
      from pytest_report_extras import Mime
      report.attach(
          "This is a XML document:",
          body="<root><child>text</child></root>",
          mime=Mime.XML
      )
      report.attach(
          comment="This is a JSON document:",
          source="path/to/file",
          mime="application/json"
      )
      report.attach(
          comment="This is a JSON document:",
          source="path/to/file",
          mime="json"
      )


* Example adding links

.. code-block:: python

  @pytest.mark.tms("TEST-3, TEST-9")
  @pytest.mark.issues("PROJ-123, PROJ-456")
  @pytest.mark.link("https://example.com")
  @pytest.mark.link(uri="https://wikipedia.org", name="Wikipedia")
  def test_link_markers(report)
      # Your test goes here


Sample CSS file
===============

.. code-block:: css

  .col-links a {
      text-decoration: none;
  }
  
  .logwrapper {
      min-height: unset;
      max-height: 100px;
  }
  
  .logwrapper .log {
      min-height: unset;
  }
  
  .extras_td {
      width: 320px;
  }
  
  .extras_td_div {
      text-align: center;
  }
  
  .extras_description {
      color: black;
      font-size: x-large;
      margin-top: 0px;
      margin-bottom: 24px;
  }
  
  .extras_params_title {
      font-size: medium;
      font-weight: bold;
      color: black;
  }
  
  .extras_params_key {
      font-size: 14px;
      color: #999;
      padding-left: 30px;
  }
  
  .extras_params_value {
      font-size: 14px;
      color: black;
  }
  
  .extras_exception {
      color: red;
  }
  
  .extras_separator {
      height: 2px;
      background-color: gray;
  }
  
  .extras_comment {
      font-family: monospace;
      color: blue;
  }
  
  .extras_pre {
      margin-left: 30px;
      color: black;
  }
  
  .extras_failure {
      font-family: monospace;
      color: red;
  }
  
  .extras_skip {
      font-family: monospace;
      color: orange;
  }
  
  .extras_video {
      width: 300px;
      height: 170px;
  }
  
  .extras_td svg {
      width: 300px;
      height: 170px;
  }
  
  .extras_image {
      border: 1px solid black;
      width: 300px;
      height: 170px;
      object-fit: cover;
      object-position: top;
  }
  
  .extras_page_src {
      font-size: 12px;
      color: #999;
  }
  
  .extras_iframe {
      margin-left: 30px;
      margin-right: 30px;
      margin-top: 15px;
      inline-size: -webkit-fill-available;
      background-color: #faf0e6;
  }


Sample reports
==============

* Pytest-html sample report

.. image:: demo-pytest.png

* Allure sample report

.. image:: demo-allure.png
