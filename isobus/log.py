import logging
import logging.handlers

# create log
log = logging.getLogger('isobus')
log.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# File handler
fh = logging.FileHandler('isobus.log', mode='w')

# Syslog handler
sh = logging.handlers.SysLogHandler()
sh.ident = 'isobus '

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s : %(message)s')
slFormatter = logging.Formatter('%(levelname)s %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
fh.setFormatter(formatter)
sh.setFormatter(slFormatter)

# TODO: Make a function to start logging to file / stdout/ stderr? Or use syslog?

# add sh to log
log.addHandler(sh)
