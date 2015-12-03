#!/usr/bin/python

try:
    import config
except:
    raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

from subprocess import Popen, PIPE
from threading import Thread
from Queue import Queue, Empty

ioQ = Queue()
commandPath = "/home/xmanj/Tools/dump1090/dump1090"
args = "--aggressive --gain 40 --net"
argList = args.split(" ")
bufSz = 30

def streamWatcher(identifier, stream):

    for line in stream:
        ioQ.put((identifier, line))

    if not stream.closed:
        stream.close()


def printer():
    while True:
        try:
            # Block for 1 second.
            item = ioQ.get(True, 0.1)
        except Empty:
            # No output in either streams for a second. Are we done?
            if proc.poll() is not None:
                break
        else:
            identifier, line = item
            print identifier + ':', line.replace("\n", "")

popenCmd = [commandPath] + argList
proc = Popen(popenCmd, bufsize=bufSz, stdout=PIPE, stderr=PIPE)

Thread(target=streamWatcher, name='stdoutWatcher', args=('STDOUT', proc.stdout)).start()
Thread(target=streamWatcher, name='stderrWatcher', args=('STDERR', proc.stderr)).start()
Thread(target=printer, name='printer').start()