from PyQt4.QtCore import *
from PyQt4.QtGui import *


class ColorBox(QFrame):
    # code snippet adapted from https://gist.github.com/justinfx/5793291
    # also see
    # http://pyqt.sourceforge.net/Docs/PyQt4/qframe.html
    colorchanged  =  pyqtSignal()

    def __init__(self,col=Qt.green,parent=None):
        super(ColorBox,self).__init__(parent)
        #pdb.set_trace()
        qcol = QColor(col)
        self.rgb = (qcol.red(), qcol.green(), qcol.blue())

        self.bgColor = QColor(qcol)
        self.setFixedHeight(20)
        self.setFixedWidth(20)
        self.setFrameStyle(1)
        self.updateStyle()

    def updateStyle(self):
        self.setStyleSheet("QWidget { border-color: rgba(0,0,0,0)}")
        self.setStyleSheet("QWidget { background-color: rgb(%d,%d,%d) }" % self.rgb)

    def mousePressEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            col = QColorDialog.getColor(self.bgColor, self)

            if col.isValid() and col != self.bgColor:
                #pyqtRemoveInputHook()
                #pdb.set_trace()
                #pyqtRestoreInputHook()
                self.rgb = (col.red(), col.green(), col.blue())
                self.setStyleSheet("QWidget { background-color: rgb(%d,%d,%d) }" % self.rgb)
                self.bgColor = col
                self.colorchanged.emit()

    @property
    def getRGB(self):
        return self.rgb

    def setRGB(self,rgbtuple):
        self.rgb=rgbtuple
        self.updateStyle()
        self.colorchanged.emit()
