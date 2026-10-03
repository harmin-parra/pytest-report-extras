=====
Usage
=====


Options
=======

These are the options that can be added to the ``pytest.ini`` file.

.. confval:: extras_screenshots

   TYPE: ``str``

   DEFAULT VALUE: ``all``

The screenshots to add in the report.

Accepted values:

* ``all``: Include all gathered screenshots in the report.

* ``last``: Include only the last screenshot of each test in the report. Works only when using **pytest-html** plugin and if the API has been previously called during the test execution.

* ``fail``: Include only the last screenshot of each failed and skipped test in the report. Works only when using **pytest-html** plugin and if the API has been previously called during the test execution.

* ``none``: Exclude all screenshots in the report.

.. confval:: extras_sources

   TYPE: ``bool``

   DEFAULT VALUE: ``False``

Whether to include gathered webpage sources in the report.

.. confval:: extras_attachment_indent

   TYPE: ``int``

   DEFAULT VALUE: ``4``

The indent to use for attachments.

Accepted values: any positive integer.

.. confval:: extras_issue_link_pattern

   TYPE: ``str``

   DEFAULT VALUE: ``None``

The pattern for the issues links. Example: ``https://bugtracker.com/issues/{}``

.. confval:: extras_tms_link_pattern

   TYPE: ``str``

   DEFAULT VALUE: ``None``

The pattern for the test-case links. Example: ``https://tms.com/tests/{}``

.. confval:: extras_links_column

   TYPE: ``str``

   DEFAULT VALUE: ``all``

The type of links to display in the **Links** columns of the pytest report.

Accepted values:

* ``all``: Display all links

* ``issue``: Display issue links

* ``tms``: Display test case links

* ``link``: Display web links:

* ``none``: Display no links

.. confval:: extras_title

   TYPE: ``str``

   DEFAULT VALUE: ``"Test Report"``

The test report title

API
===

The plugin provides the function scoped ``report`` fixture.

.. code-block:: python

  def test_example(report):
    ...
    ...

Methods
-------

report.screenshot
~~~~~~~~~~~~~~~~~

.. code-block:: python

  screenshot(
      comment: str,
      target: WebDriver | WebElement | Page | Locator = None,
      full_page: bool = True,
      page_source: bool = False,
      escape_html: bool = True
  )

Add a step with screenshot

PARAMETERS:

* **comment**: Comment of the test step.
* **target**: The screenshot target. (*optional*)
* **full_page**: Whether to take a full page screenshot.
* **page_source**: Whether to include the webpage HTML source.
* **escape_html**: Whether to escape HTML characters in the comment.

report.attach
~~~~~~~~~~~~~

.. code-block:: python

  attach(
      comment: str,
      body: str | bytes | dict | list[str] = None,
      source: str = None,
      mime: Mime | str = None,
      escape_html: bool = True
  )

Add a step with attachment.

PARAMETERS:

* **comment**: Comment of the test step.
* **body**: The content/body of the attachment.

  Type of **body** parameter:

  * ``str``:

    - for XML, JSON, YAML, CSV or TXT attachments.
    - for image, video and audio attachments in base64 string format.
  * ``bytes``: for image, video and audio attachments.
  * ``dict``: for JSON attachments.
  * ``list[str]``: for list-uri attachments.

* **mime**: The attachment mime type.

  The supported mime types are:

  - ``report.Mime.JSON``, ``application/json`` or ``json``.
  - ``report.Mime.XML``, ``application/xml`` or ``xml``.
  - ``report.Mime.YAML``, ``application/yaml`` or ``yaml``.
  - ``report.Mime.MP3``, ``audio/mpeg`` or ``mp3``.
  - ``report.Mime.OGA``, ``audio/ogg`` or ``oga``.
  - ``report.Mime.BMP``, ``image/bmp`` or ``bmp``.
  - ``report.Mime.GIF``, ``image/gif`` or ``gif``.
  - ``report.Mime.JPEG``, ``image/jpeg`` or ``jpeg``.
  - ``report.Mime.PNG``, ``image/png`` or ``png``.
  - ``report.Mime.SVG``, ``image/svg+xml`` or ``svg``.
  - ``report.Mime.CSV``, ``text/csv`` or ``csv``.
  - ``report.Mime.HTML``, ``text/html`` or ``html``.
  - ``report.Mime.TEXT``, ``text/plain`` or ``text``.
  - ``report.Mime.URI``, ``text/uri-list`` or ``uri``.
  - ``report.Mime.MP4``, ``video/mp4`` or ``mp4``.
  - ``report.Mime.OGV``, ``video/ogg`` or ``ogv``.
  - ``report.Mime.WEBM``, ``video/webm`` or ``webm``.


Marks
-----

pytest.mark.issue
~~~~~~~~~~~~~~~~~

Add issue links to the report

``@pytest.mark.issue(keys: str, icon: str)``

PARAMETERS

* **keys**: issue keys separated by comma.
* **icon**: HTML entity code for the icon/emoji. Default value: ``&#128030;`` 🐞

.. code-block:: python

  @pytest.mark.issue("BUG-1234", "&#128030;")

pytest.mark.tms
~~~~~~~~~~~~~~~

Add test-case links to the report

``@pytest.mark.tms(keys: str, icon: str)``

PARAMETERS

* **keys**: test-case keys separated by comma.
* **icon**: HTML entity code for the icon/emoji. Default value: ``&#128221;`` 📝

.. code-block:: python

  @pytest.mark.tms("TMS-123, TMS-456")

pytest.mark.link
~~~~~~~~~~~~~~~~

Add webpage links to the report

``@pytest.mark.link(url: str, name: str, icon: str)``

PARAMETERS

* **url**: webpage URL.
* **name**: Name to display instead of the URL.
* **icon**: HTML entity code for the icon/emoji. Default value: ``&#127758;`` 🌍

.. code-block:: python

  @pytest.mark.link("https://www.wikipedia.org", "Wikipedia")

EXAMPLES
========

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

Example with Selenium
~~~~~~~~~~~~~~~~~~~~~

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


Example with Playwright
~~~~~~~~~~~~~~~~~~~~~~~

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


Example with attachments
~~~~~~~~~~~~~~~~~~~~~~~~

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


Example with links
~~~~~~~~~~~~~~~~~~

.. code-block:: python

  @pytest.mark.tms("TEST-3")
  @pytest.mark.issue("PROJ-123, PROJ-456")
  @pytest.mark.link("https://example.com")
  @pytest.mark.link(uri="https://wikipedia.org", name="Wikipedia")
  @pytest.mark.link(uri="https://wikipedia.org", name="Wikipedia", icon="&#129373;")
  def test_link_markers(report)
      pass

Example with pytest-bdd (cucumber)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
