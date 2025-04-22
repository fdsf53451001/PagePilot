from PyQt6 import QtCore, QtGui, QtWidgets
import sys

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 533)
        self.lineEdit = QtWidgets.QLineEdit(parent=Dialog)
        self.lineEdit.setGeometry(QtCore.QRect(80, 20, 191, 22))
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(parent=Dialog)
        self.label.setGeometry(QtCore.QRect(20, 25, 45, 15))
        self.label.setObjectName("label")
        self.checkBox = QtWidgets.QCheckBox(parent=Dialog)
        self.checkBox.setGeometry(QtCore.QRect(290, 20, 85, 19))
        self.checkBox.setObjectName("checkBox")
        self.textBrowser = QtWidgets.QTextBrowser(parent=Dialog)
        self.textBrowser.setGeometry(QtCore.QRect(20, 55, 361, 421))
        self.textBrowser.setObjectName("textBrowser")
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=Dialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(20, 495, 241, 22))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.pushButton = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton.setGeometry(QtCore.QRect(330, 490, 51, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(270, 490, 51, 28))
        self.pushButton_2.setObjectName("pushButton_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.lineEdit.setText(_translate("Dialog", "https://www.google.com"))
        self.label.setText(_translate("Dialog", "Website"))
        self.checkBox.setText(_translate("Dialog", "Refresh"))
        self.textBrowser.append("ready")
        self.pushButton.setText(_translate("Dialog", "Send"))
        self.pushButton_2.setText(_translate("Dialog", "Voice"))


class TaskView(QtWidgets.QDialog):
    """專注於界面的顯示和交互"""
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
    
    def add_status_text(self, text):
        self.ui.textBrowser.append(text)