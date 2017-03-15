python-isobus
=============

Implementation of the ISOBUS (ISO11783) standard in Python. Currently only the VT client control function is implemented.

Installation
-------------------------
Using pip, this will also install dependencies if necessary:

::

    pip install git+git://github.com/jboomer/python-isobus.git

This will also install a command line tool: vtclient

Alternatively, clone this repo and run

::

    setup.py install


TODO
----
- VTClient : Notifier for activation messages
- VTClient : Implement aux client (aux maintenance)
- Make common 'ISOBUS CF' class w/ address claim etc.
- Implement receiving TP session
- Implement BAM
- Unit tests!
- VTClient : List connected VTs
- VTClient : Get versions command
- Test w/Windows
- comments in scripts
- VTClient : GUI interface w/ pygtk or pyQT
- Use sphinx documentation for API
- VTClient : Read aliases from file, to be distributed with pool?
