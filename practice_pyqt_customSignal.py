from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import *
import sys


class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setGeometry(300, 300, 800, 600)

    def initUI(self):
        self.message = lineEdit()
        self.engine = webEngine()
        self.content = Content()

        self.message.returnPressed.connect(self.message.onEntered)
        self.message.sendText.connect(self.content.textGaved)
        self.content.htmlChanged.connect(self.engine.changed)

        # message.returnPressed.connect(message.onEntered)

        self.engine.setHtml(self.content.html)

        vbox = QVBoxLayout()
        vbox.addWidget(self.engine)
        vbox.addWidget(self.message)

        self.setLayout(vbox)


class webEngine(QWebEngineView):
    def __init__(self):
        super().__init__()

    @pyqtSlot(str)
    def changed(self, text):
        print("changed")
        self.setHtml(text)


class lineEdit(QLineEdit):
    sendText = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def onEntered(self):
        print("onEntered")
        _txt = self.text()
        self.setText("")
        self.sendText.emit(_txt)


class Content(QObject):
    htmlChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.html = "<html>\n<body>Hello, world!</body>\n</html>"

    @pyqtSlot(str)
    def textGaved(self, text):
        print("textGaved")
        self.html = f"<html>\n<body><a href='{text}'>{text}</a></body>\n</html>"
        self.htmlChanged.emit(self.html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
