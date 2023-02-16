==============
faker-file-api
==============
REST API for `faker-file`_.

.. External references

.. _faker-file: https://faker-file.readthedocs.io/en/latest/

Installation
============
.. code-block:: sh

    pip install -r requirements.txt

Running
=======
Development
-----------
.. code-block:: sh

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Production
----------
.. code-block:: sh

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 4

Testing
=======
.. code-block:: sh

    pytest .

Writing documentation
=====================

Keep the following hierarchy.

.. code-block:: text

    =====
    title
    =====

    header
    ======

    sub-header
    ----------

    sub-sub-header
    ~~~~~~~~~~~~~~

    sub-sub-sub-header
    ^^^^^^^^^^^^^^^^^^

    sub-sub-sub-sub-header
    ++++++++++++++++++++++

    sub-sub-sub-sub-sub-header
    **************************

License
=======
MIT

Support
=======
For security issues contact me at the e-mail given in the `Author`_ section.

For overall issues, go to `GitHub <https://github.com/barseghyanartur/faker-file-api/issues>`_.

Author
======
Artur Barseghyan <artur.barseghyan@gmail.com>
