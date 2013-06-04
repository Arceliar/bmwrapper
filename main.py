#!/usr/bin/python2.7

import outgoing
import incoming
import asyncore

def run():
    outserv = outgoing.outgoingServer(('localhost', 12345), None)
    inserv = incoming.incomingServer('localhost', 12344)
    try:
        print "Press Ctrl+C to exit."
        asyncore.loop()
    except KeyboardInterrupt:
        print "Exiting..."
        print "Sockets might get stuck open..."
        print "Just wait a minute before restarting the program..."
        pass

if __name__ == '__main__':
    run()
