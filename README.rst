python-isobus
=============

Implementation of the ISOBUS (ISO11783) standard in Python. Currently only a VT client. CLI for VT client can be found in the vtclient.py module.


TODO
----
- VTClient : Notifier for activation messages
- VTClient : Implement aux client (aux maintenance)
- Make common 'ISOBUS CF' class w/ address claim etc.
- Implement receiving TP session
- Implement BAM
- VTClient : List connected VTs
- VTClient : Get versions command
- Test w/Windows & Python 2
- comments in scripts
- VTClient : GUI interface w/ pygtk or pyQT
- Use sphinx documentation
- VTClient : Read aliases from file, to be distributed with pool?
