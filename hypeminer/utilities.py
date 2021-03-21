#!/usr/bin/env python
from datetime import datetime
import os
import json


def to_epoch(timestamp, is_safe=True, milliseconds=False):
	if is_safe:
		y = int(timestamp[0:4])
		mo = int(timestamp[4:6])
		d = int(timestamp[6:8])
		h = int(timestamp[8:10])
		mi = int(timestamp[10:12])
		s = int(timestamp[12:14])
	else:
		y = int(timestamp[0:4])
		mo = int(timestamp[5:7])
		d = int(timestamp[8:10])
		h = int(timestamp[11:13])
		mi = int(timestamp[14:16])
		s = int(timestamp[17:19])
	epoch = datetime(y, mo, d, h, mi, s).timestamp()
	if milliseconds:
		return int(epoch * 1000)
	else:
		return int(epoch)


# from https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])


def save_to_json(filename, the_object):
	with open(filename, 'w') as f_out:
		f_out.write(json.dumps(the_object, indent=4))
