============
Installation
============

Requirements
------------

The plugin requires Python version 3.11 or higher.

* ``pytest >= 8.4.0``
* ``pyyaml >= 6.0.2``


Optional modules
----------------

* ``pytest-html >= 4.0.0``        if using **pytest-html**
* ``pytest-bdd >= 8.1.0``         **pytest-html** and/or **allure-pytest** is required if using **pytest-bdd**. Do not use **allure-pytest-bdd** plugin with **pytest-report-extras**.
* ``selenium >= 4.11.0``          if using **Selenium**.
* ``pytest-playwright >= 0.4.3``  if using **Playwright**.
* ``allure-pytest >= 2.13.2``     if using **Allure**.

Note: this plugin doesn't integrate with **allure-pytest-bdd**


Installing pytest-report-extras
--------------------------------

.. code-block:: bash

  $ pip install pytest-report-extras

