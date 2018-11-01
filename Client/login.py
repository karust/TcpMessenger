from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, QWidget, QDialog
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import QSize, Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from network import Net
import os, sys 


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent) 
        self.cwd = os.path.abspath(os.path.dirname(sys.argv[0]))+"/"
        self.initUI()
        
    def initUI(self):
        uic.loadUi(self.cwd+"ui/login.ui", self)
        self.setWindowTitle("Login")
        self.error    = QLabel()

        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        portNumber = "([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
        ipRegex = QRegExp("^"+ipRange+"\\."+ipRange+"\\."+ipRange+"\\."+ipRange+"\\:"+portNumber+"$")
        ipValidator = QRegExpValidator(ipRegex, self)  
        self.adress.setValidator(ipValidator)
    
    def check(self, name, password, adress):
        nameCorr, passCorr, adressCorr = True, True, True
        # TODO: cehck pass and adress
        if (name or adress) == None:
            return False, False, False
        if len(name) < 3:
            nameCorr = False
        if not adress:
            adressCorr = False
        return (nameCorr, passCorr, adressCorr)

    def keyPressEvent(self, qKeyEvent):
        if qKeyEvent.key() == Qt.Key_Return: 
            self.accept()

    def connError(self, isError=True):
        if isError:
            self.error.setText("Server is unreacheable")
            self.error.setStyleSheet('''color: rgb(200, 0, 0);''')  
            self.vBox.addWidget(self.error) 
        else:
            pass
            #self.error.setParent(None)

    def notification(self, msg=""):
        infoBox = QtWidgets.QMessageBox()
        infoBox.setIcon(QtWidgets.QMessageBox.Warning)
        infoBox.setText(msg)
        infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        infoBox.exec_()
    
    @staticmethod
    def start(nameErr=None, passErr=None, adrErr=None,
              nameData=None, passData=None, adrData=None, connErr=False):
        # TODO: Rewrite totally, recursion is unclear
        dialog = LoginDialog()
        if connErr:
            dialog.connError(True)
        else:
            dialog.connError(False)
        if nameErr:
            dialog.nameLabel.setText(nameErr)
            dialog.nameLabel.setStyleSheet('color: red')
        else:
            dialog.name.setText(nameData)

        if passErr:
            dialog.passLabel.setText(passErr)
            dialog.passLabel.setStyleSheet('color: red')
        else:
            dialog.password.setText(passData)

        if adrErr:
            dialog.adressLabel.setText(adrErr)
            dialog.adressLabel.setStyleSheet('color: red')
        else:
            dialog.adress.setText(adrData)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = dialog.name.text()
            password = dialog.password.text()
            adress = dialog.adress.text()

            nameCorr, passCorr, adressCorr = dialog.check(name, password, adress)
            #print("InLog:", nameCorr, passCorr, adressCorr)
            if nameCorr & passCorr & adressCorr:
                dialog.accept()
                return name, password, adress
            else:
                nameErr, passErr, adrErr = None, None, None
                if not nameCorr:
                    nameErr = "Name should be at least 3 symbols"
                    name = None
                if not passCorr:
                    passErr = "Wrong password"
                    password = None
                if not adressCorr:
                    adrErr = "Incorrect adress:port"
                    adress = None
                name, password, adress = dialog.start(nameErr, passErr, adrErr, name, password, adress)
                dialog.destroy()
                nameCorr, passCorr, adressCorr = dialog.check(name, password, adress)
                if nameCorr & passCorr & adressCorr:
                    return name, password, adress
        else:
            os._exit(1)