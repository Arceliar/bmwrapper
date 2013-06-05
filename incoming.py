import socket
import threading
import email.mime.text
import email.mime.image
import email.mime.multipart
import bminterface
import re

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
      print "Parsing msg %i of %i" % (msgID+1, msgCount)
      dateTime, toAddress, fromAddress, subject, body = bminterface.get(msgID)
      msgSizes.append(len(makeEmail(dateTime, toAddress, fromAddress, subject, body)))
    return msgSizes

def handleStat(data):
    print "Running STAT"
    msgSizes = _getMsgSizes()
    msgCount = len(msgSizes)
    msgSizeTotal = 0
    for msgSize in msgSizes:
      msgSizeTotal += msgSize
    returnData = '+OK %i %i\r\n' % (msgCount, msgSizeTotal)
    print "Answering STAT"
    return returnData

def handleList(data):
    print "Running LIST"
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
    print "Answering LIST"
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
    print data.split()
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
    print data
    if len(data) == 1:
      refdata = bminterface.getUIDLforAll()
    else:
      refdata = bminterface.getUIDLforSingle(int(data[1])-1)
    print refdata
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
      msg = email.mime.text.MIMEText(body[0])
    else:
      msg = email.mime.multipart.MIMEMultipart('mixed')
      bodyText = email.mime.text.MIMEText(body[0])
      body = body[1:]
      msg.attach(bodyText)
      for item in body:
        itemType, itemData = [0], [0]
        try:
          itemType, itemData = item.split(';', 1)
          itemType = itemType.split('/', 1)
        except:
          print "Could not parse message type"
          pass
        if itemType[0] == 'image':
          try:
            itemData = itemData.lstrip('base64,').strip(' ').strip('\n').decode('base64')
            img = email.mime.image.MIMEImage(itemData)
            img.add_header('Content-Disposition', 'attachment')
            msg.attach(img)
          except:
            print "MIME exception occurred"
            #print "data was..." + itemData.encode('base64')
            pass
    msg['To'] = toAddress
    msg['From'] = fromAddress
    msg['Subject'] = subject
    msg['Date'] = dateTime
    return msg.as_string()
    
def parseBody(body):
    #TODO Fix this so it parses for images, strips them from the text, decodes and appends them.
    returnData = []
    text = ''
    searchString = '<img[^>]*'
    attachment = re.search(searchString, body, re.DOTALL)
    while attachment:
      imageCode = body[attachment.start():attachment.end()]
      imageDataRange = re.search('src=("|\')(.*)("|\')', imageCode, re.DOTALL)
      imageData=''
      if imageDataRange:
        try:
          imageData = imageCode[imageDataRange.start()+5:imageDataRange.end()-1].lstrip('data:')
        except:
          pass
      if imageData:
        returnData.append(imageData)
      body = body[:attachment.start()] + body[attachment.end():]
      attachment = re.search(searchString, body, re.DOTALL)
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


def incomingServer(host, port):
    popthread = threading.Thread(target=incomingServer_main, args=(host, port))
    popthread.daemon = True
    popthread.start()

def incomingServer_main(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    try:
        if host:
            hostname = host
        else:
            hostname = "localhost"
        while True:
            sock.listen(1)
            conn, addr = sock.accept()
            try:
                conn = ChatterboxConnection(conn)
                conn.sendall("+OK server ready")
                while True:
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
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

