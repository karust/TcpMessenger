import socket
from threading import Thread
import time
from struct import pack, unpack
from binascii import hexlify
from PyQt5 import QtCore


def prepack(f, *args):
    return pack('=' + f, *args)


class Contact:
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid

class Group:
    def __init__(self, name, gid, members):
        self.name = name
        self.gid = gid
        self.members = members

class Message:
    def __init__(self, group, text, id):
        self.text = text
        self.id = id
        self.group = group
        self.stickerPack = None
        self.stickerNum = None
        self.time_name = ""


class Net(QtCore.QThread):
    contactUpd = QtCore.pyqtSignal(Contact)
    groupUpd = QtCore.pyqtSignal(list)
    messageUpd = QtCore.pyqtSignal(Message)
    errorEvent = QtCore.pyqtSignal(str)
    def __init__(self):
        QtCore.QThread.__init__(self)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._isStop = False
        self.roffset = 0
        self.data = None

    def rByte(self):
        data = unpack("B", self.data[self.roffset:self.roffset+1])[0]
        self.roffset += 1
        return data
    def rShort(self):
        data = unpack("H", self.data[self.roffset:self.roffset+2])[0]
        self.roffset += 2
        return data
    def rInt(self):
        data = unpack("I", self.data[self.roffset:self.roffset+4])[0]
        self.roffset += 4
        return data
    def rLong(self):
        data = unpack("Q", self.data[self.roffset:self.roffset+8])[0]
        self.roffset += 8
        return data
    def rString(self, length):
        data = unpack("{0}s".format(length), self.data[self.roffset:self.roffset+length])[0]
        self.roffset += length
        return data

    def connect(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((ip, port))

    def disconnect(self):
        try:
            self.s.shutdown(1)
        except:
            pass
        self.s.close()
        #self.stop()

    def run(self):
        self._isStop = False
        while not self._isStop:
            size = self.s.recv(2)
            if size:
                size = unpack("H", size)[0]
                data = self.s.recv(size)
                opcode = unpack("H", data[:2])[0]
                #print("Data:", hexlify(data))

                self.roffset = 2
                self.data = data
                if opcode == 255:
                    self.handleContacts()
                elif opcode == 254:
                    self.handleMessage()
                elif opcode == 253:
                    self.handleSticker()
                elif opcode == 252:
                    self.handleGroups()
                elif opcode == 251:
                    self.handleError()
                else:
                    print("Unknown opcode:", opcode)

    def stop(self):
        self._isStop = True
        self.join()

    def isRunning(self):
        return not self._isStop

    def send(self, data, opcode):
        dlen = len(data)
        self.s.send(
            pack('=HH{0}s'.format(dlen),
                dlen+2,
                opcode,
                data
                 ))

    def register(self, name, passw, adr):
        name = name.encode("utf-8")
        passw = passw.encode("utf-8")

        data = prepack("H{0}sH{1}s".format(len(name), len(passw)),
        len(name), name, len(passw), passw)

        self.send(data, opcode=4)
        data = self.s.recv(1024)

        if len(data) > 0:
            print("Data:", hexlify(data))
            size, opcode = unpack("HH", data[:4])
            print(size, opcode)
            if opcode == 401:
                return False
            elif opcode == 200:
                uid = unpack("Q", data[4:])[0]
                return uid
            else:
                return None

    def startup(self):
        self.getContacts()

    # opc=10, ALL (byte), nameLen (Short), name, ID (Long)
    def getContacts(self, name=None, id=None):
        all = False
        if name and len(name) > 3:
            data = prepack("BH{0}s".format(len(name)),
            all, len(name), name.encode("utf-8"))
        elif id:
            data = prepack("BHL", all, 0, id)
        else:
            all = True
            data = prepack("B", all)
        self.send(data, opcode=10)

    def handleContacts(self):
        count = self.rByte()
        for _ in range(count):
            uid = self.rLong()
            nameLen = self.rShort()
            name = self.rString(nameLen).decode("utf-8")
            contact = Contact(name=name, uid=uid)
            self.contactUpd.emit(contact)

    # opc = 1, group?(B), ID(Q), tlen(H), text(S)
    def sendMessage(self, group, Id, message):
        message = message.encode("utf-8")
        tlen = len(message)
        data = prepack("BQH{0}s".format(tlen), group, Id, tlen, message)
        self.send(data, opcode=1)

    #opc=254, group?(B), uid(Q), tlen(H), text(S)
    def handleMessage(self):
        group = self.rByte()
        id = self.rLong()
        tlen = self.rShort()
        text = self.rString(tlen).decode("utf-8")
        message = Message(group = group, text=text, id=id)
        #print("Message from {0} : {1}".format(uid, text))
        self.messageUpd.emit(message)

    # opc=2, uid(Q), stPack(H), stNum(H)
    def sendSticker(self, group, id, stPack, stNum):
        data = prepack("BQHH", group, id, stPack, stNum)
        self.send(data, opcode=2)

    #opc=253, group?(B), uid(Q), stPack(H), stNum(H)
    def handleSticker(self):
        group = self.rByte()
        id = self.rLong()
        stPack = self.rShort()
        stNum = self.rShort()
        message = Message(group=group, text="", id=id)
        message.stickerPack = stPack
        message.stickerNum = stNum
        self.messageUpd.emit(message)

    # opc=3, tlen(H), text(S)
    def createGroup(self, gname):
        gname = gname.encode("utf-8")
        tlen = len(gname)
        data = prepack("H{0}s".format(tlen), tlen, gname)
        self.send(data, opcode=3)

    # opc=5, GID(Q), UID(Q)
    def delAddUserGroup(self, gid, uid):
        #nlen = len(userName)
        data = prepack("QQ", gid, uid)
        self.send(data, opcode=5)
	
    # opc=6, GID(Q)
    def joinGroup(self, gid):
        data = prepack("Q", gid)
        self.send(data, opcode=6)
    
    # opc=7, count (B), nlen(H), name(S)
    def getGroups(self, name="", count=0):
        nlen = len(name)
        if len(name) >= 3:
            data = prepack("BH{0}s".format(nlen), count, nlen, name)
        else:
            data = prepack("BH", count, nlen)
        self.send(data, opcode=7)

    #opc=252, Count (byte), nameLen (Short), name(text), ID (Long), Members (Int)
    def handleGroups(self):
        count = self.rByte()
        groups = []
        for _ in range(count):
            nameLen = self.rShort()
            name = self.rString(nameLen).decode("utf-8")
            gid = self.rLong()
            members = self.rInt()
            group = Group(name=name, gid=gid, members=members)
            groups.append(group)
        self.groupUpd.emit(groups)
    
    #opc=251, errLen(H), err(S) 
    def handleError(self):
        errLen = self.rShort()
        err = self.rString(errLen)
        self.errorEvent.emit(err.decode("utf-8"))

