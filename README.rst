|Show Logo|

===========
TestHelpers
===========

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

.. |Show Logo| image:: http://dl.eveprosper.com/podcast/logo-colour-17_sm2.png
    :target: http://eveprosper.com