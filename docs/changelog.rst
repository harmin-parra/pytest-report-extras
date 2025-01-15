=========
Changelog
=========


1.3.0
=====

**Change**

* Remove deprecated code.

**Improvement**

* CSS file is automatically added if ``-css`` option is not provided.


1.2.2
=====

**Feature**

* Limited support for the ``--self-contained-html`` option of the **pytest-html** plugin.


1.2.1
=====

**Feature**

* Support for attachments of mime type: ``image/bmp``, ``image/gif``, ``image/jpeg``, ``image/png``, ``image/svg+xml`` and ``image/tiff``

**Bug fix**

* The plugin was still making calls to deprecated code.
* Better handling of attachments with other mime types (ex: ``application/pdf``).


1.2.0
=====

**Change**

* Modification of the algorithm related to attachments. The ``report.step`` method is going to be deprecated.

**Features**

* Posibility to add links to the tests report.
* New INI option to customize the indentation of XML, JSON and YAML attachments.
* Support for attachments of mime type: ``text/csv``, ``text/html``  and ``text/uri-list``


1.1.0
=====

**Bug fix**

* Exception handling when formatting invalid XML, JSON and YAML documents added in comments.
 
**Improvements**

* The **Allure** report can be generated if the **pytest-html** option is not used.
* Removal of comments in XML documents added in comments.


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
