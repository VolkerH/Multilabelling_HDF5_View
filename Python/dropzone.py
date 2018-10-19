from PyQt4.QtCore import *
from PyQt4.QtGui import *

class DropZone(QLabel):
    # inspired partly by http://rowinggolfer.blogspot.de/2010/04/pyqt4-modelview-drag-drop-example.html
    """
    Creates a label widget that acts as a target area for drag and drop actions.
    emits a newFilesSignal when files are dropped onto it
    """
    newFilesSignal  =  pyqtSignal(list)

    def __init__(self, title="Dropzone", width=600, height=300, parent=None):
        super(DropZone, self).__init__(parent)
        self.setFixedHeight(height)
        self.setFixedWidth(width)
        self.setAcceptDrops(True)
        #self.setText("Drop HDF5 Files Here")
        self.setText(title)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QWidget { border-color: rgba(0,0,0,0)}")
        self.setStyleSheet("QWidget { background-color: rgb(128,128,128) }")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.set_bg(True)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.set_bg()
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
               print(url.path())
            event.acceptProposedAction()
            self.newFilesSignal.emit(event.mimeData().urls())
            self.set_bg()
        else:
            super(DropZone,self).dropEvent(event)

    def set_bg(self, active=False):
        if active:
            val = "background:yellow;"
        else:
            val = "background:grey;"
        self.setStyleSheet(val)