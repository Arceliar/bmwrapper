#!/usr/bin/python2.7

import outgoing
import incoming
import asyncore
import threading
import sys
import logging

def run():
    logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s', level=logging.DEBUG)

    run_event = threading.Event()
    run_event.set()

    outserv = outgoing.outgoingServer(('localhost', 12345), None)
    inserv = incoming.incomingServer('localhost', 12344, run_event)

    try:
        logging.info("Press Ctrl+C to exit.")
        asyncore.loop()
    except KeyboardInterrupt:
        logging.info("Exiting...")
        run_event.clear()
        logging.debug("waiting for threads...")
        inserv.join()
        logging.debug("all threads done...")
        sys.exit(0)

if __name__ == '__main__':
    run()
