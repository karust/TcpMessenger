from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, QWidget, QTableWidgetItem
from PyQt5.QtWidgets import QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from network import *
from custom import *
from login import LoginDialog
from groups import GroupsDialog
import os
import sys
import sqlite3 as db


class MainWindow(QMainWindow):
    trigger = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.cwd = os.path.abspath(os.path.dirname(sys.argv[0]))+"/"
        self.loginDialog = LoginDialog(parent=self)
        self.conn_data, self.db_conn = self.getLoginData()
        self.net = Net()
        self.myid = None
        self.initUI()
        self.events()
        self.login()
        self.net.start()
        
        self.isSticker = False
        self.contacts = []
        self.conversations = {} # uid : [messages]

        self.groups = []
        self.group_conversations = {} # uid : [messages]
        self.net.getGroups()
        self.lastInd = 0
        self.Tabs.setCurrentIndex(0)

    def initUI(self):
        QtWidgets.QMainWindow.__init__(self)
        uic.loadUi(self.cwd+"ui/main.ui", self)
        ico = self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon)
        self.setWindowIcon(ico)
        self.setWindowTitle("T0p Messenger - 2k18")
        self.SticketsWidget = StickerWidget(parent=self.Stickers)
        self.SticketsWidget.cwd = self.cwd
        self.SticketsWidget.loadStickers()
        self.setStyle()
        self.initEvents()

    def setStyle(self):
        self.SendBtn.setStyleSheet("""
        .QPushButton {
            background-image: url(cl.png);
            background-color: #6d65ff;
            }
        .QPushButton::hover {
            background-image: url(cl.png);
            background-color: #8795ff;
            }
        """)

    def initEvents(self):
        self.ContactsList.itemSelectionChanged.connect(self.contactSelectionChanged)
        self.GroupsList.itemSelectionChanged.connect(self.groupSelectionChanged)
        menubar = self.menuBar()
        self.SendBtn.clicked.connect(self.sendMessage)
        self.StickerBtn.clicked.connect(self.stickerContactsBtn)
        self.Tabs.currentChanged.connect(self.tabChanged)

        reloginAction = QAction('&Relogin', self)
        reloginAction.setShortcut('Ctrl+R')
        reloginAction.triggered.connect(self.login)

        fileMenu = menubar.addMenu('&Account')
        fileMenu.addAction(reloginAction)

        crGr = QAction('&Create group', self)
        crGr.setShortcut('Ctrl+G')
        crGr.triggered.connect(self.createGroup)

        groups = menubar.addMenu('&Groups')
        groups.addAction(crGr)

    def events(self):
        self.net.contactUpd.connect(self.setContact)
        self.net.groupUpd.connect(self.setGroups)
        self.net.messageUpd.connect(self.newMessage)
        self.net.errorEvent.connect(self.notification)
        self.SticketsWidget.stickerEv.connect(self.sendSticker)

    @staticmethod
    def getLoginData():
        dbconn = db.connect("data.db")
        conn_data = {"adress":"127.0.0.1:5555", "login":"qwe123", "pass":"123123"}
        return conn_data, dbconn

    def login(self):
        name, passw, adr = self.conn_data["login"], self.conn_data["pass"], self.conn_data["adress"]

        #print("DB: ", name, passw, adr)

        registered, unreacheable = False, False
        while not registered:
            nameCorr, passCorr, adressCorr = self.loginDialog.check(
                name=name, password=passw, adress=adr)
            #print(nameCorr, passCorr, adressCorr)
            if nameCorr & passCorr & adressCorr:
                try:
                    ip, port = adr.split(":")[0], int(adr.split(":")[1])
                    
                    self.net.connect(ip=ip, port=port)
                    #self.net.start()
                    registered = self.net.register(name, passw, adr)
                    unreacheable = False
                except Exception as e:
                    unreacheable = True
                    print("Connection error:", e)

                if registered == False:
                    #self.notification("Wrong name or password")
                    #name, passw, adr = None, None, None
                    name, passw, adr = self.loginDialog.start(
                    nameData=name, passData=passw, adrData=adr, connErr=unreacheable)
                #elif registered:
                #    registered = True
                elif registered == None:
                    #self.notification("Server unreacheable")
                    name, passw, adr = self.loginDialog.start(
                    nameData=name, passData=passw, adrData=adr, connErr=unreacheable)
                elif registered:
                    self.myid = registered
            else:
                name, passw, adr = self.loginDialog.start(
                    nameData=name, passData=passw, adrData=adr)
                #print("Login:", name, password, adr)
            if not registered:
                #print(123)
                try:
                    self.net.disconnect()
                except:
                    pass
                #self.net.stop()
        self.net.startup()

    def relogin(self):
        if self.net.isRunning():
            self.net.stop()
        else:
            self.net.start()

    def keyPressEvent(self, qKeyEvent):
        print(qKeyEvent.key())
        if qKeyEvent.key() == QtCore.Qt.Key_Return: 
            self.sendMessage()
        else:
            super().keyPressEvent(qKeyEvent)

    def contactSelectionChanged(self):
        selected = self.ContactsList.currentRow()
        self.setMessages(selected)

    def groupSelectionChanged(self):
        selected = self.GroupsList.currentRow()
        self.setMessages(selected)

    def tabChanged(self):
        ind = self.Tabs.currentIndex()
        if ind == 2:
            self.lastInd = self.lastInd
        else:
            self.lastInd = ind

    def sendMessage(self):
        text = self.Text.text()
        if text == "":
            return
        elif text[:5] == "/kick":
            self.kick_group(text)
        elif self.lastInd == 0:
            message = Message(group=False,text=text, id=self.myid)
            message.time_name = "{0} at {1}".format("Me", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            selected = self.ContactsList.currentRow()
            cont = self.contacts[selected]
            self.net.sendMessage(group=False, Id=cont.uid, message=text)
            #if cont.uid != self.myid:
            self.conversations[cont.uid] = self.conversations.get(cont.uid, [])
            self.conversations[cont.uid].append(message)
            self.setMessage(message, right=True)
        elif self.lastInd == 1:
            message = Message(group=True,text=text, id=self.myid)
            message.time_name = "{0} at {1}".format("Me", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            selected = self.GroupsList.currentRow()
            gr = self.groups[selected]
            self.net.sendMessage(group=True, Id=gr.gid, message=text)
            self.group_conversations[gr.gid] = self.group_conversations.get(gr.gid, [])
            self.group_conversations[gr.gid].append(message)
            self.setMessage(message, right=True)

        self.Text.setText("")

    def newMessage(self, message):
        message.time_name = "{0} at {1}".format("User[{0}]".format(message.id), strftime("%Y-%m-%d %H:%M:%S", gmtime()))        
        print(message)
        if message.group:
            self.group_conversations[message.id] = self.group_conversations.get(message.id, [])
            self.group_conversations[message.id].append(message)
            if self.lastInd == 1:
                self.groupSelectionChanged()
                #if message.stickerNum != None:
                #    self.setSticker(message)
                #else:
                #    self.setMessage(message)
        else:
            self.conversations[message.id] = self.conversations.get(message.id, [])
            self.conversations[message.id].append(message)
            if self.lastInd == 0:
                self.contactSelectionChanged()
                #if message.stickerNum != None:
                #    self.setSticker(message)
                #else:
                #    self.setMessage(message)

    def setMessage(self, message, right=False):
        msg = MessageElem(right=right)
        msg.setTextUp(message.time_name)
        text = '\n'.join(message.text[i:i+50] for i in range(0, len(message.text), 50))
        msg.setTextDown(text)
        msg.setIcon(self.cwd+'ui/ico.png')

        msgItem = QListWidgetItem(self.Messages)
        msgItem.setSizeHint(msg.sizeHint())

        self.Messages.addItem(msgItem)
        self.Messages.setItemWidget(msgItem, msg)
        self.Messages.setCurrentItem(msgItem)

    def setMessages(self, id):
        self.Messages.clear()
        if self.lastInd == 0:
            try:
                cont = self.contacts[id]
                self.ContactName.setText("Contact: " + cont.name)   
                convers = self.conversations[cont.uid]
            except Exception:
                return

        elif self.lastInd == 1:
            try:
                gr = self.groups[id]
                self.ContactName.setText("Group: " + gr.name)   
                convers = self.group_conversations[gr.gid]
            except Exception:
                return
            
        for mess in convers:
            if mess.stickerNum != None:
                if mess.id == self.myid:
                    self.setSticker(mess, right=True)
                else:
                    self.setSticker(mess)
                continue
            if mess.id == self.myid:
                self.setMessage(mess, right=True)
            else:
                self.setMessage(mess)

    def stickerContactsBtn(self):
        if not self.isSticker:
            self.StickerBtn.setText("C")
            QTabWidget.setCurrentIndex(self.Tabs, 0)
        else:
            self.StickerBtn.setText(":-(")
            QTabWidget.setCurrentIndex(self.Tabs, 2)
        self.isSticker = not self.isSticker
        self.Ceontacts.setVisible(False)
    
    def sendSticker(self, message):
        if self.lastInd == 0:
            selected = self.ContactsList.currentRow()
            cont = self.contacts[selected]
            message.uid = cont.uid
            self.conversations[cont.uid] = self.conversations.get(cont.uid, [])
            self.conversations[cont.uid].append(message)
            self.net.sendSticker(False, cont.uid, message.stickerPack, message.stickerNum)
        elif self.lastInd == 1:
            selected = self.GroupsList.currentRow()
            gr = self.groups[selected]
            message.uid = gr.gid
            self.group_conversations[gr.gid] = self.group_conversations.get(gr.gid, [])
            self.group_conversations[gr.gid].append(message)
            self.net.sendSticker(True, gr.gid, message.stickerPack, message.stickerNum)
        message.time_name = "{0} at {1}".format("Me", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        self.setSticker(message, right=True)


    def setSticker(self, message, right=False):
        st = Sticker(right=right)
        st.setSticker(self.cwd+'ui/sticker/{0}.png'.format(message.stickerNum))
        st.setAvatar(self.cwd+'ui/ico.png')
        st.setTextDown(message.time_name)
        listItem = QListWidgetItem(self.Messages)
        listItem.setSizeHint(st.sizeHint())
        self.Messages.addItem(listItem)
        self.Messages.setItemWidget(listItem, st)
        self.Messages.setCurrentItem(listItem)

    def setContact(self, contact):
        self.contacts.append(contact)
        
        contWidg = Contact()
        if contact.uid == self.myid:
            contWidg.setName("Saved messages")
        else:
            contWidg.setName(contact.name)
        #contWidg.setCount('1')
        #contWidg.highlight()
        contWidg.setStatus(" ")
        contWidg.setIcon(self.cwd + 'ui/ico.png')

        item = QListWidgetItem(self.ContactsList)
        item.setSizeHint(contWidg.sizeHint())

        self.ContactsList.addItem(item)
        self.ContactsList.setItemWidget(item, contWidg)
        self.ContactsList.setCurrentItem(item)

    def setGroups(self, groups):
        self.GroupsList.clear()
        for g in groups:
            self.setGroup(g)

    def setGroup(self, group):
        self.groups.append(group)

        grWdg = Group()
        grWdg.setTextUp(group.name)
        grWdg.setTextDown("Members: {0}".format(group.members))
        grWdg.setIcon(self.cwd+'ui/ico.png')
        grWdg.setCount(str(group.gid))
        grWdg.gid = group.gid
        item = QListWidgetItem(self.GroupsList)
        item.setSizeHint(grWdg.sizeHint())
        grWdg.join.connect(self.joinGroup)
        grWdg.leave.connect(self.leave_group)
        self.GroupsList.addItem(item)
        self.GroupsList.setItemWidget(item, grWdg)
        self.GroupsList.setCurrentItem(item)

    def createGroup(self):
        group = GroupsDialog(parent=self)
        name = group.start()
        if name:
            self.net.createGroup(name)
        elif name == None:
            self.notification(msg="Name too short")

    def joinGroup(self, gid):
        self.net.joinGroup(gid)

    def leave_group(self, gid):
        self.net.delAddUserGroup(gid, self.myid)

    def kick_group(self, cmd):
        if self.lastInd == 1:
            selected = self.GroupsList.currentRow()
            gr = self.groups[selected]
            try:
                print(cmd[6:])
                id = int(cmd[6:])
                self.net.delAddUserGroup(gr.gid, uid=id)
            except Exception as e:
                print(e)
                self.notification("Provide id of user")
        else:
            self.notification("Group not selected")

    def notification(self, msg, retry=False):
        infoBox = QtWidgets.QMessageBox()
        infoBox.setIcon(QtWidgets.QMessageBox.Warning)
        infoBox.setText(msg)
        if retry:
            infoBox.setWindowTitle("Connection error")
            infoBox.setStandardButtons(QtWidgets.QMessageBox.Retry)
        else:
            infoBox.setWindowTitle("Error")
            infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        infoBox.exec_()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    window = MainWindow()
    window.show()

    app.exec_()
    try:
        sys.exit()
    except:
        pass