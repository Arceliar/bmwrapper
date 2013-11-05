#!/usr/bin/python2.7

import outgoing
import incoming
import asyncore
import threading
import sys

def run():
    run_event = threading.Event()
    run_event.set()
    outserv = outgoing.outgoingServer(('localhost', 12345), None)
    inserv = incoming.incomingServer('localhost', 12344, run_event)
    try:
        print "Press Ctrl+C to exit."
        asyncore.loop()
    except KeyboardInterrupt:
        print "Exiting..."
        run_event.clear()
        print "waiting for threads..."
        inserv.join()
        print "all threads done..."
        sys.exit(0)

if __name__ == '__main__':
    run()
