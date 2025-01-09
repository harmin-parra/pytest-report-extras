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

* ``last``:   Include only the last screenshot of each test in the report. Works only if the API has been previously called during the test execution in order to store the reference of the WebDriver (Selenium) or Page (Playwright) object.

Default value: ``all``

----

* ``extras_sources``

Whether to include gathered webpage sources in the report.

Default value: ``False``

----

* ``extras_description_tag``

The HTML tag for the test description (test docstring).

Accepted values: ``h1``, ``h2``, ``h3``, ``p`` or ``pre``

Default value: ``pre``

----

* ``extras_attachment_indent``

The indent to use for attachments.

Accepted values: any positive integer.

Default value: ``4``


API
===

The function scoped fixture ``report`` provides the following methods:

To add a step with screenshot:

.. code-block:: python

  screenshot(
      comment: str,                              # Comment of the test step.
      target: WebDriver | WebElement | Page | Locator = None,  # The page or element.
      full_page: bool = True,                     # Whether to take a full page screenshot.
      page_source: bool = False,                  # Whether to include the webpage HTML source.
      escape_html: bool = False                   # Whether to escape HTML characters in the comment.
  )
  
To add a step with attachment:

.. code-block:: python

  attach(
      comment: str,                                 # Comment of the test step.
      body: str | bytes | Dict | List[str] = None,  # The content/body of the attachment.
      source: str = None,                           # The filepath of the attachment.
      mime: str | Mime = None,                      # The attachment mime type.
      escape_html: bool = False                     # Whether to escape HTML characters in the comment.
  )
  
  # Type of body parameter:
  #    str: - for XML, JSON, YAML, CSV or TXT attachments
  #         - for image attachments if it is a base64 string
  #    bytes: for image attachments
  #    Dict: for JSON attachments
  #    List[str]: for list-uri attachments
  
  # The supported mime types are:
  #    report.Mime.image_bmp
  #    report.Mime.image_gif
  #    report.Mime.image_jpeg
  #    report.Mime.image_png
  #    report.Mime.image_svg_xml
  #    report.Mime.image_tiff
  #    report.Mime.text_csv
  #    report.Mime.text_html
  #    report.Mime.text_plain
  #    report.Mime.text_uri_list
  #    report.Mime.application_json
  #    report.Mime.application_xml
  #    report.Mime.application_yaml


To add a link to the report:

.. code-block:: python

  link(
      uri: str,              # The uri.
      name: str = None       # The text of the anchor tag.
  )
  

Limitations
===========

* Limited support for the ``--self-contained-html`` option of the **pytest-html** plugin. The report still contains links for attachments of unsopported mime types.

* No support for any kind of parallel tests execution (multi-treads, multi-tabs or multi-windows).

* For Playwright, only **sync_api** is supported.


Example
=======

When using the **pytest-html** plugin (with the ``--html`` option), an external CSS file needs be provided with the ``--css`` option.


Command-line invocation
-----------------------

If using pytest-html report:

.. code-block:: bash

  pytest --html=/path/to/report --css=/path/to/css

If using Allure report:

.. code-block:: bash

  pytest --alluredir=/path/to/allure-results

If using both reports:

.. code-block:: bash

  pytest --html=/path/to/report --css=/path/to/css --alluredir=/path/to/allure-results


Sample ``pytest.ini`` file
--------------------------

.. code-block:: ini

  extras_description_tag = h1
  extras_attachment_indent = 4
  extras_screenshots = all
  extras_sources = False


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
      report.screenshot("Get the webpage to test", driver)
      driver.find_element(By.ID, "my-text-id").send_keys("Hello World!")
      report.screenshot("<h1>Set input text</h1>", driver, full_page=True, escape_html=False)
      driver.find_element(By.NAME, "my-password").send_keys("password")
      report.screenshot(comment="Another comment", target=driver)
      report.screenshot("Comment without screenshot")
      report.screenshot(comment="Comment without screenshot")
      driver.quit()


* Example using Playwright

.. code-block:: python

  def test_with_playwright(page: Page, report):
      """
      This is a test using Playwright
      """
      page.goto("https://www.selenium.dev/selenium/web/web-form.html")
      report.screenshot("Get the webpage to test", page)
      report.screenshot(comment="Get the webpage to test", target=page, full_page=False)


* Example adding attachments

.. code-block:: python

  def test_attachments(report):
      """
      This is a test adding XML & JSON attachments
      """
      xml_body = """
          <note>  
              <to>John</to>  
              <from>Diana</from>  
              <heading>Reminder</heading>  
              <body>Don't forget me this weekend!</body>  
          </note>"""
          
      report.attach(
          "This is a XML document:",
          body=xml_body,
          mime=report.Mime.application_xml
      )
	  
      report.attach(
          comment="This is a JSON document:",
          source="/path/to/file",
          mime=report.Mime.application_json
      )


* Example adding links

.. code-block:: python

  def test_links(report):
      """
      This is a test adding links
      """
      report.link("https://en.wikipedia.org")
      report.link("https://wikipedia.org", "Wikipedia")
      report.link(uri="https://wikipedia.org", name="Wikipedia")


Sample CSS file
===============

.. code-block:: css

  .logwrapper {
      max-height: 100px;
  }

  .extras_td {
      width: 320px;
      /* text-align: center; */
  }

  .extras_td_div {
      text-align: center;
  }
 
  .extras_separator {
      height:2px;
      background-color: gray;
      /* display: none; */
  }
  
 .extras_description {
    color: black;
    font-size: larger
  }

  .extras_exception {
      color: red;
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
