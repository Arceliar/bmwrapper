bmwrapper
========

bmwrapper is a poorly hacked together python script to let Thunderbird and PyBitmessage communicate, similar to AyrA's (much better) application.

I'm on linux and don't feel like dealing with wine, so I wrote this to fill the same role for myself.

The script operates by running a POP server on localhost:12344, and an SMTP server on localhost:12345.

The pop server is based on pypopper: http://code.activestate.com/recipes/534131-pypopper-python-pop3-server/

The SMTP server is based on SMTP sink server: http://djangosnippets.org/snippets/96/

.dok's text client for the bitmessage daemon was referenced as well: <PUT URL HERE>

It makes a reasonable effort to interact nicely with people using only PyBitmessage. Outgoing email messages are parsed, with email headers stripped, and attached images are converted to a base64 encoded embedded img tag. Incoming messages are likewise parsed for image tags, and the contents are (usually) converted back to an email attachment. Some effort is made to convert the standard email block quotes into PyBitmessage's '---' line separated quotes.

WARNING
-------

There are a few issues you should be aware of before running this.

- If you are not careful with your email client configuration, bmwrapper may hit a race condition and eat up all your memory unless you kill it.
- After exiting, the POP server has a tendency to leave an abandoned socket open for a minute or so, preventing the application from being restarted immediately.
- In order to comply with protocol, the POP server trashes each message from the PyBitmessage inbox after it has been delivered to an email client.
- I have not tested this heavily. It works for me, but there's no guarantee it won't eat your inbox and spit nothing back out, then eat all your memory and lock your machine up.

I wrote this for my own personal use. Don't expect me to provide technical support. I've just released it as a proof of concept / reference for anyone who wants to write a version that doesn't suck.
