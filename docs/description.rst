===========
Description
===========


This plugin works by adding extra content to the HTML report generated by **pytest-html** and **allure**.

The plugin is suitable for both front-end tests (Selenium or Playwright) and back-end tests.

The test steps are composed by the following parts:

* Comment or description.

* Screenshot (if applicable).

* Source of the webpage where the screenshot was taken (if applicable).

**pytest-report-extras** integrates with:

* `Selenium <https://www.selenium.dev/>`_

* `Playwright <https://playwright.dev/python/>`_

* `Allure Report <https://allurereport.org/>`_

Docstring of tests are also included in the report, as mean to provide a long description of tests.
Therefore, you are highly encouraged to document your tests with docstrings.


History of the project
======================

**pytest-report-extras** is the successor of the `pytest-webtest-extras <https://pytest-webtest-extras.readthedocs.io/>`_ project. The latter is now deprecated.

**pytest-webtest-extras** was primarily focus on front-end tests (Selenium or Playwright).

**pytest-report-extras** is a more general-purpose test report plugin that can also be used for back-end tests without screenshots.
