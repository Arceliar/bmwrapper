bmwrapper
========

bmwrapper is a poorly hacked together python script to let Thunderbird and PyBitmessage communicate, similar to AyrA's (generally much better) application: ﻿Bitmessage2Mail.

I'm on Linux, and don't feel like dealing with wine. So I wrote this to fill the same role as B2M, until it is ported or the source code is released.

The script (usually) parses outgoing messages to strip the ugly email header information and put quoted text in PyBitmessage’s '---’ delimited form. Attached images are included, base64 encoded, in an img tag. Incoming messages are likewise parsed to reconstruct a email, with attachment. This works...most of the time, and I’ve tried to make it fail gracefully when something goes wrong.

Running
-------

First make sure you have the api configured in your key.dat (check bitmessage.org's wiki for details). If you're running in portable mode, you need to put your bmwrapper scripts in the same directory as your keys.dat file. If you run bitmessage in normal mode, it should try to detect where your keys.dat is saved.

Then do this:

    python main.py

That’s about it.

The script operates by running a POP server on localhost:12344, and an SMTP server on localhost:12345.

The pop server is based on pypopper: http://code.activestate.com/recipes/534131-pypopper-python-pop3-server/

The SMTP server is based on SMTP sink server: http://djangosnippets.org/snippets/96/

.dok's text client for the bitmessage daemon was cannibalized as well: https://github.com/Dokument/PyBitmessage-Daemon

Client configuration: (On Thunderbird, YMMV with other clients)
Use anything as a username/password, and something along the lines of BM-AddressGoesHere@bm.addr as your email--though everything after the @ is arbitrary and will be stripped.
For the incoming mail server: POP, localhost, port 12344, don’t use SSL and use ‘normal password’ for authentication.
For the outgoing mail server: SMTP, localhost, port 12345, don’t use SSL, no password for authentication.

Send p2p messages the obvious way, appending something like “@bm.addr” on the “To" address, just to make the address look valid for your email client.

To send a broadcast, send a message from an address to itself. The script will notice this and send a broadcast instead of a p2p message.

WARNING
-------

There are a few issues you should be aware of before running this.

- If you are not careful with your email client configuration, bmwrapper may hit a race condition and eat up all your memory unless you kill it.
- After exiting, the POP server has a tendency to leave an abandoned socket open for a minute or so, preventing the application from being restarted immediately.
- In order to comply with the protocol, the POP server trashes each message from the PyBitmessage inbox after it has been delivered to an email client. This is not immediately visible if you have the PyBitmessage GUI running in the background--they won't disappear until you restart. You have been warned.
- I have not tested this heavily. It works for me, but there's no guarantee it won't eat your inbox and spit nothing back out, then eat all your memory and lock your machine up.

I wrote this for my own personal use. Don't expect me to provide much/any technical support. I've just released it for anyone interested in using it. If something breaks, and it affects me, I’ll probably get around to fixing it eventually...

Useful Thunderbird Settings
--------------------------

Account Settings->Composition&Addressing has a checkbox to disable HTML formatting, and settings to change default quote behavior. I have mine set to place my reply above the quote, my signature below my reply and above the quote. If you use these settings, then when bmwrapper parses for leading '>' and strips them, moving the text below a '-------' line, your outgoing reply messages will look (mostly) consistent with PyBitmessage.

If you want to remove the reply header: (The line that says who wrote the last message, and when you received it)
- Edit->Preferences->Advanced->Configuration Editor
- mailnews.reply_header_type = 0
- mailnews.reply_header_originalmessage = (I changed this to an empty string)
    
You can leave the address of the person you're replying to, but not the timestamp, by changing the first setting to 1 instead.

Also useful, if you want messages to be threaded:
- mail.strict_threading = false
- mail.thread_without_re = true
- mailnews.localizedRe = AW,Aw,Antwort,VS,Vs,SV,Sv,Svar

The last option tells thunderbird to cound those strings as another form of Re. Without it, any message beginnign with "AW:" and the others will end up in a separate thread. If you subscribe to any mailing lists with people who use localized email clients, then I highly recommend using this setting. Without it, you may find that the thread forks whenever somebody with a localized client replies.

You then need to select a folder where you want your messages to be threaded, and set View->Sort_By->Threaded. Then right click the folder, select properties, and click Repair Folder. That'll get it to parse the subject lines again and thread messages. The order can still get messed up, if BM received them out of order, but they're at least grouped correctly (most of the time).

Speaking of folders, I made one for each mailing list and shared address I'm subscribed to. You can set up filters to redirect messages to their folder, based on their To/From addresses. This makes pseudomailinglists and shared address 'chans' much more usable.
