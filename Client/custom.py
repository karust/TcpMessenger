import sys
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QMenu, QTableWidget
from PyQt5 import Qt
from PyQt5.QtCore import QTimer, Qt as Qtc
from time import gmtime, strftime
from PyQt5.QtCore import QSize, pyqtSignal
from network import Message


class _MessageItem(QWidget):
    kickEv = pyqtSignal()
    def __init__(self, parent = None, right=False):
        super(_MessageItem, self).__init__(parent)
        self.VBox = QVBoxLayout()
        self.message  = QLabel()
        self.nickname    = QLabel()
        self.avatar      = QLabel()

    def contextMenuEvent(self, event):    
        menu = QMenu(self)
        kick = menu.addAction("Kick user")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if action == kick:
            self.kickEv.emit()


class MessageElem (_MessageItem):
    def __init__ (self, parent = None, right = False):
        super(MessageElem, self).__init__(parent) 
        self.VBox.addWidget(self.nickname)
        self.VBox.addWidget(self.message)   

        if right:
            self.nickname.setAlignment(Qt.Qt.AlignRight)
            self.message.setAlignment(Qt.Qt.AlignRight)
            self.VBox.setAlignment(Qt.Qt.AlignCenter)
            
            self.allQHBoxLayout  = QHBoxLayout()
            self.allQHBoxLayout.setAlignment(Qt.Qt.AlignRight)
            self.avatar.setAlignment(Qt.Qt.AlignRight)

            self.allQHBoxLayout.addLayout(self.VBox, 0)
            self.allQHBoxLayout.addWidget(self.avatar, 0)
            self.setLayout(self.allQHBoxLayout)

        else:
            self.allQHBoxLayout  = QHBoxLayout()
            self.allQHBoxLayout.addWidget(self.avatar, 0)
            self.allQHBoxLayout.addLayout(self.VBox, 1)
            self.setLayout(self.allQHBoxLayout)

        self.nickname.setStyleSheet('''
            color: rgb(200, 0, 0);
        ''')
        self.message.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')

    def setTextUp (self, text):
        self.nickname.setText(text)

    def setTextDown (self, text):
        self.message.setText(text)

    def setIcon (self, imagePath):
        self.avatar.setPixmap(QPixmap(imagePath).scaled(32, 32))


class Sticker (_MessageItem):
    def __init__ (self, parent = None, right=False):
        super(Sticker, self).__init__(parent)
        self.sticker    = QLabel()

        self.message.setAlignment(Qt.Qt.AlignRight)
        self.sticker.setAlignment(Qt.Qt.AlignCenter)

        if right:
            self.avatar.setAlignment(Qt.Qt.AlignRight)
        else:
            self.avatar.setAlignment(Qt.Qt.AlignLeft)

        self.VBox.addWidget(self.avatar)
        self.VBox.addWidget(self.sticker)
        self.VBox.addWidget(self.message)

        self.setLayout(self.VBox)
        self.message.setStyleSheet('''
            color: rgb(0, 0, 0);
        ''')

    def setTextDown (self, text):
        self.message.setText(text)

    def setSticker (self, imagePath):
        self.sticker.setPixmap(QPixmap(imagePath).scaled(220, 220))

    def setAvatar (self, imagePath):
        self.avatar.setPixmap(QPixmap(imagePath).scaled(32, 32))


class Contact (QWidget):
    def __init__ (self, parent = None):
        super(Contact, self).__init__(parent)
        self.textQVBoxLayout = QVBoxLayout()
        self.textUpQLabel    = QLabel()
        
        self.textDownQLabel  = QLabel()
        self.textDownQLabel.setWordWrap(True)
        self.textUpQLabel.setWordWrap(True)

        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QHBoxLayout()
        self.iconQLabel      = QLabel()
        self.textCount    = QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.allQHBoxLayout.addWidget(self.textCount, 0)
        self.setLayout(self.allQHBoxLayout)

        # setStyleSheet
        self.textUpQLabel.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')
        self.textDownQLabel.setStyleSheet('''
            color: rgb(0, 255, 0);
        ''')

    def setName (self, text):
        self.textUpQLabel.setText(text)

    def setCount (self, text):
        self.textCount.setText(text)

    def highlight(self):
        self.textCount.setStyleSheet("""
        .QLabel {
            background-color: yellow;
            }
        """)
        #QTimer.singleShot(1000, lambda: self.countAnimate(change_color = not change_color))

    def setStatus (self, text):
        self.textDownQLabel.setText(text)

    def setIcon (self, imagePath):
        self.iconQLabel.setPixmap(QPixmap(imagePath).scaled(32, 32))

    def contextMenuEvent(self, event):    
        menu = QMenu(self)
        addContact = menu.addAction("Add to contacts")
        removeContact = menu.addAction("Remove from contacts")
        addToGroup = menu.addAction("Add to group")
        about = menu.addAction("About")
    
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if action == addContact:
            print("Add contact")
        elif action == removeContact:
            print("Remove Contact")
        elif action == addToGroup:
            print("Add to group")
        elif action == about:
            print("About")


class Group (QWidget):
    join = pyqtSignal(int)
    leave = pyqtSignal(int)
    about = pyqtSignal(int)
    def __init__ (self, parent = None):
        super(Group, self).__init__(parent)
        self.textQVBoxLayout = QVBoxLayout()
        self.textUpQLabel    = QLabel()
        
        self.textDownQLabel  = QLabel()
        self.textDownQLabel.setWordWrap(True)
        self.textUpQLabel.setWordWrap(True)

        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QHBoxLayout()
        self.iconQLabel      = QLabel()
        self.textCount    = QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.allQHBoxLayout.addWidget(self.textCount, 0)
        self.setLayout(self.allQHBoxLayout)
        self.gid = None
        # setStyleSheet
        self.textUpQLabel.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')
        self.textDownQLabel.setStyleSheet('''
            color: rgb(0, 22, 0);
        ''')

    def setTextUp (self, text):
        self.textUpQLabel.setText(text)

    def setCount (self, text):
        self.textCount.setText(text)

    def newMessage(self):
        self.textCount.setStyleSheet("""
        .QLabel {
            background-color: yellow;
            }
        """)
        #QTimer.singleShot(1000, lambda: self.countAnimate(change_color = not change_color))

    def setTextDown (self, text):
        self.textDownQLabel.setText(text)

    def setIcon (self, imagePath):
        self.iconQLabel.setPixmap(QPixmap(imagePath).scaled(32, 32))

    def contextMenuEvent(self, event):    
        menu = QMenu(self)
        joinGroup = menu.addAction("Join group")
        leaveGroup = menu.addAction("Leave group")
        about = menu.addAction("About")

        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if action == joinGroup:
            self.join.emit(self.gid)
        elif action == leaveGroup:
            self.leave.emit(self.gid)
        elif action == about:
            self.about.emit(self.gid)


class ImageWidget(QWidget):
    def __init__(self, imagePath, parent):
        super(ImageWidget, self).__init__(parent)
        self.picture = QPixmap(imagePath)
        self.resize(1,1)
        self.set
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.picture)


class StickerWidget(QTableWidget):
    stickerEv = pyqtSignal(Message)
    def __init__(self, parent=None):
        super(StickerWidget, self).__init__(parent)
        self.cwd = None
        self.setShowGrid(False)
        self.setColumnCount(2)
        self.setRowCount(20)
        self.setGeometry(0,0,235,721)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setWindowFlags(Qtc.FramelessWindowHint)
        self.events()

    def setImage(self, row, col, imagePath):
        image = ImageWidget(imagePath, self)
        self.setCellWidget(row, col, image)
    
    def loadStickers(self):
        left = True
        self.setColumnWidth(0, 109)
        self.setColumnWidth(1, 109)
        for i in range(40):
            #image = ImageWidget(self.cwd+"ui/sticker/{0}.png".format(i+1), self)
            image      = QLabel()
            pixmap = QPixmap(self.cwd+"ui/sticker/{0}.png".format(i+1))
            image.setPixmap(pixmap.scaled(128, 128))
  
            if left:
                self.setCellWidget(i//2, 0, image)
            else:
                self.setCellWidget(i//2, 1, image)
            self.setRowHeight(i, 150)
            left = not left
    
    def events(self):
        self.cellClicked.connect(self.chooseSticker)

    def chooseSticker(self):
        st = Message(group=False,text="", id=0)
        st.stickerPack = 0
        st.stickerNum = self.currentRow()*2 + self.currentColumn() + 1
        self.stickerEv.emit(st)