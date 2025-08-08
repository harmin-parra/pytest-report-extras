=========
Changelog
=========


1.3.7
=====

**Bug fix**

* Impossible to execute **pytest** when the **pytest-html** plugin is not installed.

**Feature**

* Support for **pytest-bdd** tests. If using **Allure**, install the **allure-pytest** plugin instead of **allure-pytest-bdd**.


1.3.6
=====

**Feature**

* Addition of ``extras_links_column`` INI option to filter the type of links to display in the **Links** column of the pytest report.

**Improvement**

* CSS class added for error messages related to attachments.

**Change**

* This version of the plugin requires **pytest** v8.4.0 or later.


1.3.5
=====

**Bug fix**

* Wrong dependency version in ``pyproject.toml`` file.


1.3.4
=====

**Feature**

* Link icons can be customized.

**Change**

* The ``@pytest.mark.issues`` marker has been renamed to ``@pytest.mark.issue``.

**Bug fix**

* Error parsing attachment from a source file when generating only the **Allure** report.


1.3.3
=====

**Features**

* New design for the runtest header report.
* Addition of runtest header report for tests with ``error`` execution status (failed and skipped tests during setup).

**Change**

* The ``extras_description_tag`` INI option has been removed.


1.3.2
=====

**Features**

* The ``extras_screenshots`` INI option can also accept ``fail`` or ``none`` value.
* Support for attachments of mime type: ``audio/mpeg`` and ``audio/ogg``.
* New ``extras_title`` INI option to customize the test report title.

**Changes**

* Deprecated code has been removed.
* The plugin requires python version 3.11 or later.


1.3.1
=====

**Features**

* Support for attachments of mime type: ``image/svg+xml``, ``video/mp4``, ``video/ogg`` and ``video/webm``.
* Mime types of attachments can also be set with file extensions.
* Introduction of new ``Report.Mime`` shorter attributes for mime types. The long old ones will be deprecated in the next major release.

**Improvement**

* Error-handling improvements.

**Change**

* Screenshot and webpage source files are named using a uuid generator.


1.3.0
=====

**Feature**

* New INI options to define link patterns for issues and test-cases and new decorators to add links to the report.

**Improvements**

* A default CSS style sheet is automatically added if ``--css`` option is not provided.
* Usage errors are logged in the standard error stream (stderr).
* Test parameters via the ``@pytest.mark.parametrize`` decorator are added to the report.

**Changes**

* The ``report.link`` method will be deprecated in the next major release.
* The ``report.step`` deprecated method has been removed.


1.2.2
=====

**Feature**

* Limited support for the ``--self-contained-html`` option of the **pytest-html** plugin.


1.2.1
=====

**Feature**

* Support for attachments of mime type: ``image/bmp``, ``image/gif``, ``image/jpeg``, ``image/png`` and ``image/svg+xml``

**Bug fixes**

* The plugin was still making calls to deprecated code.
* Better handling of attachments with other mime types (ex: ``application/pdf``).


1.2.0
=====

**Features**

* Posibility to add links to the tests report.
* New INI option to customize the indentation of XML, JSON and YAML attachments.
* Support for attachments of mime type: ``text/csv``, ``text/html``  and ``text/uri-list``

**Change**

* Modification of the algorithm related to attachments. The ``report.step`` method is going to be deprecated.


1.1.0
=====

**Bug fix**

* Exception handling when formatting invalid XML, JSON and YAML documents added in comments.
 
**Improvements**

* The **Allure** report can be generated if the **pytest-html** option is not used.
* Removal of comments in XML documents added as attachments.


1.0.1
=====

**Bug fix**

* Fix mistakes in the project's README file.


1.0.0
=====

**Initial release**

**Limitations**

* No support for the ``--self-contained-html`` option of the **pytest-html** plugin.

* The **Allure** report cannot be generated alone. It needs to be generated together with the **pytest-html** report.
