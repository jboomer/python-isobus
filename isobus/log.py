import logging

# create log
log = logging.getLogger('isobus')
log.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

fh = logging.FileHandler('isobus.log', mode='w')

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s : %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add ch to log
log.addHandler(fh)
