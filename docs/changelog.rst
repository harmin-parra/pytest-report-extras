=========
Changelog
=========


2.0.0
=====

**Change**

* Modification of the algorithm related to attachments.

**Features**

* Posibility to add links to the tests report.
* New ``ini`` option to customize the indentation of XML, JSON and YAML attachments.
* Support of attachments of mime type: **text/csv**, **text/uri-list**


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

**Limitation**

* The **Allure** report cannot be generated alone. It needs to be generated together with the **pytest-html** report.
