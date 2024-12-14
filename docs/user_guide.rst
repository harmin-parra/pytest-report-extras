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

* ``all``:    Include all gathered screenshots in the report.

* ``last``:   Include only the last screenshot of each test in the report. Works only if the API was been called previously during the test execution in order to store the reference of the WebDriver (Selenium) or Page (Playwright) object.

Default value: ``all``

----

* ``extras_sources``

Whether to include gathered webpage sources in the report.

Default value: ``False``

----

* ``extras_description_tag``

The HTML tag for the test description (test docstring).

Accepted values: ``h1``, ``h2``, ``h3``, ``p`` or ``pre``

Default value: ``h2``


API
===

The function scoped fixture ``report`` provides the following methods:

To add a step to the report:

.. code-block:: python

  step(
      target: WebDriver|WebElement|Page|Locator = None,
      comment: str = None,
      full_page: bool = True
      escape_html: bool = False  # Whether to escape HTML characters in the comment.
  )
  
Auxiliary method to get a code block format of a string:

.. code-block:: python

    format_code_block(content: str) -> str

Auxiliary methods to format XML, JSON and YAML strings and files:

.. code-block:: python

    format_json_file(filepath: string, indent: int = 4) -> str
    format_json_str(content: string, indent: int = 4) -> str
    format_xml_file(filepath: string, indent: int = 4) -> str
    format_xml_str(content: string, indent: int = 4) -> str
    format_yaml_file(filepath: string, indent: int = 4) -> str
    format_yaml_str(content: string, indent: int = 4) -> str


Limitations
===========

No support for any kind of parallel tests execution (multi-treads, multi-tabs or multi-windows).

For **Playwright**, only ``sync_api`` is supported.


Example
=======

| **pytest-report-extras** needs to be executed in conjunction of **pytest-html** plugin.
| Therefore, the ``--html`` option also needs to be provided.

An external CSS file needs be provided by using the **pytest-html** ``--css`` command-line option.


Command-line invocation
-----------------------

.. code-block:: bash

  pytest --html=/path/to/report --css=/path/to/css

If using Allure report:

.. code-block:: bash

  pytest --html=/path/to/report --css=/path/to/css --alluredir allure-results


Sample ``pytest.ini`` file
--------------------------

.. code-block:: ini

  extras_screenshots = all
  extras_sources = False
  extras_allure = False


Sample code
-----------

* Example using Selenium

.. code-block:: python

  def test_with_selenium(report):
      """
      This is a test using Selenium
      """
      driver = WebDriver()
      driver.get("https://www.selenium.dev/selenium/web/web-form.html")
      report.step(driver, "Get the webpage to test", full_page=False)
      driver.find_element(By.ID, "my-text-id").send_keys("Hello World!")
      report.step(driver, "<h1>Set input text</h1>", escape_html=False)
      driver.find_element(By.NAME, "my-password").send_keys("password")
      report.step(driver, "Set password")
      report.step(driver, comment="Another comment")
      report.step(comment="Comment without screenshot")
      driver.quit()


* Example using Playwright

.. code-block:: python

  def test_with_playwright(page: Page, report):
      """
      This is a test using Playwright
      """
      page.goto("https://www.selenium.dev/selenium/web/web-form.html")
      report.step(page, "Get the webpage to test")


* Example adding code-block content

.. code-block:: python

  def test_code_block(page: Page, report):
      """
      This is a test with code-block content
      """
      xml = """
          <note>  
          <to>John</to>  
          <from>Diana</from>  
          <heading>Reminder</heading>  
          <body>Don't forget me this weekend!</body>  
          </note>"""
      report.step(comment="This is a XML document:" + report.format_xml_str(xml))


Sample CSS file
===============

.. code-block:: css

  .logwrapper {
      max-height: 100px;
  }

  .extras_separator {
      height:2px;
      background-color: gray;
      /* display: none; */
  }

  .extras_td {
      width: 320px;
      /* text-align: center; */
  }

  .extras_td_div {
      text-align: center;
  }

  .extras_div {
      display: inline-block;
      text-align: center;
  }

  .extras_page_src {
      font-size: 12px;
      color: #999;
  }

  .extras_exception {
      color: black;
  }

  .extras_comment {
      font-family: monospace;
      color: blue;
  }

  .extras_failure {
      font-family: monospace;
      color: red;
  }

  .extras_skip {
      font-family: monospace;
      color: orange;
  }

  .extras_image {
      border: 1px solid black;
      width: 300px;
      height: 170px;
      object-fit: cover;
      object-position: top;
  }

  .extras_pre {
      margin-left: 30px;
      color: black;
  }


Sample reports
==============

* Pytest sample report

.. image:: demo-pytest.png

* Allure sample report

.. image:: demo-allure.png
