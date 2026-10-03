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

   TYPE: bool

   DEFAULT VALUE: ``False``

Whether to include gathered webpage sources in the report.



.. confval:: extras_attachment_indent

   TYPE: int

   DEFAULT VALUE: ``4``

The indent to use for attachments.

Accepted values: any positive integer.




.. confval:: extras_issue_link_pattern

   TYPE: str

   DEFAULT VALUE: ``None``

The pattern for the issues links (example: ``https://bugtracker.com/issues/{}``)




.. confval:: extras_tms_link_pattern

   TYPE: str

   DEFAULT VALUE: ``None``

The pattern for the test-case links (example: https://tms.com/tests/{})




.. confval:: extras_links_column

   TYPE: str

   DEFAULT VALUE: ``all``

The type of links to display in the **Links** columns of the pytest report.

Accepted values:

* ``all``: Display all links

* ``issue``: Display issue links

* ``tms``: Display test case links

* ``link``: Display web links:

* ``none``: Display no links




.. confval:: extras_title

   TYPE: str

   DEFAULT VALUE: ``Test Report``

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
      comment: str,                                 # Comment of the test step.
      body: str | bytes | dict | list[str] = None,  # The content/body of the attachment.
      source: str = None,                           # The filepath of the attachment.
      mime: Mime | str = None,                      # The attachment mime type.
      escape_html: bool = True                      # Whether to escape HTML characters in the comment.
  )

Add a step with attachment.

PARAMETERS:

* **comment**: Comment of the test step.
* **body**: The content/body of the attachment.

  Type of **body** parameter:

  * str:

    - for XML, JSON, YAML, CSV or TXT attachments.
    - for image, video and audio attachments in base64 string format.
  * bytes: for image, video and audio attachments.
  * dict: for JSON attachments.
  * list[str]: for list-uri attachments.

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
