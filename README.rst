|Show Logo|

===========
TestHelpers
===========

|Build Status| |Coverage Status| |PyPI Badge| |Docs|

Testing utility to run stripped-down test-passes on private machines

Getting Started
---------------

.. code-block:: bash

    pip install .
    RunTests --dump_config > app_local.cfg  # for writing secrets
    RunTests --config=app_local.cfg 

Meant to be installed directly or into a thin client for easy cronjobs/CLI.  

Powered by `plumbum`_

Features
========

TODO

.. _plumbum: http://plumbum.readthedocs.io/en/latest/cli.html

.. |Build Status| image:: https://travis-ci.org/EVEprosper/TestHelpers.svg?branch=master
    :target: https://travis-ci.org/EVEprosper/TestHelpers
.. |Coverage Status| image:: https://coveralls.io/repos/github/EVEprosper/TestHelpers/badge.svg?branch=master
    :target: https://coveralls.io/github/EVEprosper/TestHelpers?branch=master
.. |PyPI Badge| image:: https://badge.fury.io/py/TestHelpers.svg
    :target: https://badge.fury.io/py/TestHelpers
.. |Docs| image:: https://readthedocs.org/projects/TestHelpers/badge/?version=latest
    :target: http://TestHelpers.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |Show Logo| image:: http://dl.eveprosper.com/podcast/logo-colour-17_sm2.png
    :target: http://eveprosper.com