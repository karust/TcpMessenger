from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, QWidget, QDialog
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import QSize, Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from network import Net
import os, sys 


class GroupsDialog(QDialog):
    def __init__(self, parent=None):
        super(GroupsDialog, self).__init__(parent) 
        self.cwd = os.path.abspath(os.path.dirname(sys.argv[0]))+"/"
        self.initUI()
        
    def initUI(self):
        uic.loadUi(self.cwd+"ui/groups.ui", self)

    def keyPressEvent(self, qKeyEvent):
        if qKeyEvent.key() == Qt.Key_Return: 
            self.accept()

    def notification(self, msg=""):
        infoBox = QtWidgets.QMessageBox()
        infoBox.setIcon(QtWidgets.QMessageBox.Warning)
        infoBox.setText(msg)
        infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        infoBox.exec_()
    
    def check(self, name):
        if len(name)>3:
            return name
        else:
            return None

    @staticmethod
    def start():
        dialog = GroupsDialog()
        
        result = dialog.exec_()
        if result == QDialog.Accepted:
            text = dialog.name.text()
            return dialog.check(text)
        else:
            return False