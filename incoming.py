import socket
import threading
import email.mime.text
import email.mime.image
import email.mime.multipart
import email.header
import bminterface
import re
import select
import logging

class ChatterboxConnection(object):
    END = "\r\n"
    def __init__(self, conn):
      self.conn = conn
    def __getattr__(self, name):
      return getattr(self.conn, name)
    def sendall(self, data, END=END):
      data += END
      self.conn.sendall(data)
    def recvall(self, END=END):
      data = []
      while True:
        chunk = self.conn.recv(4096)
        if END in chunk:
          data.append(chunk[:chunk.index(END)])
          break
        data.append(chunk)
        if len(data) > 1:
          pair = data[-2] + data[-1]
          if END in pair:
            data[-2] = pair[:pair.index(END)]
            data.pop()
            break
      return "".join(data)


def handleUser(data):
    return "+OK user accepted"

def handlePass(data):
    return "+OK pass accepted"

def _getMsgSizes():
    msgCount = bminterface.listMsgs()
    msgSizes = []
    for msgID in range(msgCount):
      logging.debug("Parsing msg %i of %i" % (msgID+1, msgCount))
      dateTime, toAddress, fromAddress, subject, body = bminterface.get(msgID)
      msgSizes.append(len(makeEmail(dateTime, toAddress, fromAddress, subject, body)))
    return msgSizes

def handleStat(data):
    msgSizes = _getMsgSizes()
    msgCount = len(msgSizes)
    msgSizeTotal = 0
    for msgSize in msgSizes:
      msgSizeTotal += msgSize
    returnData = '+OK %i %i\r\n' % (msgCount, msgSizeTotal)
    logging.debug("Answering STAT: %i %i" % (msgCount, msgSizeTotal))
    return returnData

def handleList(data):
    msgCount = 0
    returnDataPart2 = ''
    msgSizes = _getMsgSizes()
    msgSizeTotal = 0
    for msgSize in msgSizes:
      msgSizeTotal += msgSize
      msgCount += 1
      returnDataPart2 += '%i %i\r\n' % (msgCount, msgSize)
    returnDataPart2 += '.'
    returnDataPart1 = '+OK %i messages (%i octets)\r\n' % (msgCount, msgSizeTotal)
    returnData = returnDataPart1 + returnDataPart2
    logging.debug("Answering LIST: %i %i" % (msgCount, msgSizeTotal))
    return returnData

def handleTop(data):
    msg = 'test'
    cmd, msgID, lines = data.split()
    msgID = int(msgID)-1
    lines = int(lines)
    dateTime, toAddress, fromAddress, subject, body = bminterface.get(msgID)
    msg = makeEmail(dateTime, toAddress, fromAddress, subject, body)
    top, bot = msg.split("\n\n", 1)
    text = top + "\r\n\r\n" + "\r\n".join(bot[:lines])
    return "+OK top of message follows\r\n%s\r\n." % text

def handleRetr(data):
    logging.debug(data.split())
    msgID = int(data.split()[1])-1
    dateTime, toAddress, fromAddress, subject, body = bminterface.get(msgID)
    msg = makeEmail(dateTime, toAddress, fromAddress, subject, body)
    return "+OK %i octets\r\n%s\r\n." % (len(msg), msg)

def handleDele(data):
    msgID = int(data.split()[1])-1
    bminterface.markForDelete(msgID)
    return "+OK I'll try..."

def handleNoop(data):
    return "+OK"

def handleQuit(data):
    bminterface.cleanup()
    return "+OK just pretend I'm gone"
    
def handleUIDL(data):
    data = data.split()
    logging.debug(data)
    if len(data) == 1:
      refdata = bminterface.getUIDLforAll()
    else:
      refdata = bminterface.getUIDLforSingle(int(data[1])-1)
    logging.debug(refdata)
    if len(refdata) == 1:
      returnData = '+OK ' + data[1] + str(refdata[0])
    else:
      returnData = '+OK listing UIDL numbers...\r\n'
      for msgID in range(len(refdata)):
        returnData += str(msgID+1) + ' ' + refdata[msgID] + '\r\n'
      returnData += '.'
    return returnData
    
def makeEmail(dateTime, toAddress, fromAddress, subject, body):
    body = parseBody(body)
    msgType = len(body)
    if msgType == 1:
      msg = email.mime.text.MIMEText(body[0], 'plain', 'UTF-8')
    else:
      msg = email.mime.multipart.MIMEMultipart('mixed')
      bodyText = email.mime.text.MIMEText(body[0], 'plain', 'UTF-8')
      body = body[1:]
      msg.attach(bodyText)
      for item in body:
        img = 0
        itemType, itemData = [0], [0]
        try:
          itemType, itemData = item.split(';', 1)
          itemType = itemType.split('/', 1)
        except:
          logging.warning("Could not parse message type")
          pass
        if itemType[0] == 'image':
          try:
            itemDataFinal = itemData.lstrip('base64,').strip(' ').strip('\n').decode('base64')
            img = email.mime.image.MIMEImage(itemDataFinal)
          except:
            #Some images don't auto-detect type correctly with email.mime.image
            #Namely, jpegs with embeded color profiles look problematic
            #Trying to set it manually...
            try:
              itemDataFinal = itemData.lstrip('base64,').strip(' ').strip('\n').decode('base64')
              img = email.mime.image.MIMEImage(itemDataFinal, _subtype=itemType[1])
            except:
              logging.warning("Failed to parse image data. This could be an image.")
              logging.warning("This could be from an image tag filled with junk data.")
              logging.warning("It could also be a python email.mime.image problem.")
          if img:
            img.add_header('Content-Disposition', 'attachment')
            msg.attach(img)
    msg['To'] = toAddress
    msg['From'] = fromAddress
    msg['Subject'] = email.header.Header(subject, 'UTF-8')
    msg['Date'] = dateTime
    return msg.as_string()
    
def parseBody(body):
    returnData = []
    text = ''
    searchString = '<img[^>]*'
    attachment = re.search(searchString, body)
    while attachment:
      imageCode = body[attachment.start():attachment.end()]
      imageDataRange = re.search('src=[\"\'][^\"\']*[\"\']', imageCode)
      imageData=''
      if imageDataRange:
        try:
          imageData = imageCode[imageDataRange.start()+5:imageDataRange.end()-1].lstrip('data:')
        except:
          pass
      if imageData:
        returnData.append(imageData)
      body = body[:attachment.start()] + body[attachment.end()+1:]
      attachment = re.search(searchString, body)
    text = body
    returnData = [text] + returnData
    return returnData

dispatch = dict(
    USER=handleUser,
    PASS=handlePass,
    STAT=handleStat,
    LIST=handleList,
    TOP=handleTop,
    RETR=handleRetr,
    DELE=handleDele,
    NOOP=handleNoop,
    QUIT=handleQuit,
    #UIDL=handleUIDL,
)


def incomingServer(host, port, run_event):
    popthread = threading.Thread(target=incomingServer_main, args=(host, port, run_event))
    popthread.daemon = True
    popthread.start()
    return popthread

def incomingServer_main(host, port, run_event):
    sock = None
    try:
        while run_event.is_set():
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                sock.listen(1)

            ready = select.select([sock], [], [], .2)
            if ready[0]:
                conn, addr = sock.accept()
                # stop listening, one client only
                sock.close()
                sock = None
                try:
                    conn = ChatterboxConnection(conn)
                    conn.sendall("+OK server ready")
                    while run_event.is_set():
                        data = conn.recvall()
                        command = data.split(None, 1)[0]
                        try:
                            cmd = dispatch[command]
                        except KeyError:
                            conn.sendall("-ERR unknown command")
                        else:
                            conn.sendall(cmd(data))
                            if cmd is handleQuit:
                                break
                finally:
                    conn.close()

    except (SystemExit, KeyboardInterrupt):
      pass
    except Exception, ex:
      raise
    finally:
        sock.close()

