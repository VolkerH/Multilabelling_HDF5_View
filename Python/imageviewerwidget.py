#!/usr/bin/env python
##
## This is adapted from sample code provided by Trolltech,
## with heavy modifications made by
## Volker.Hilsenstein@embl.de

#############################################################################
##
## Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

# TODO: maybe get rid of the whole fittowindow crap
# TODO: things get really slow when zoomed in, look into cause (maybe pixmap too large ?)
#



from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, qRgb
import qimage2ndarray

class ImageViewer(QtGui.QWidget):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.printer = QtGui.QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.layout = QtGui.QVBoxLayout()

        self.layout.addWidget(self.scrollArea)
        #self.setCentralWidget(self.scrollArea)
        self.setLayout(self.layout)
        self.createkeyboardshortcuts()
        self.fitToWindowActive = False
        self.resize(512, 512)
        self.emptyimage()

    def setimage_ndarray(self, array):
        """
        Displays a numpy array
        :param array: numpy array
        :return: nothing
        """
        image = qimage2ndarray.array2qimage(array)
        self.setimage_qimage(image)

    def setimage_qimage(self,image):
        """
        Displays a Qimage
        :param image: Qimage to be displayed
        :return:
        """
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
        #self.scaleFactor = 1.0
        #self.scaleFactor(1.0)
        #if not self.fitToWindowActive:
        #    self.imageLabel.adjustSize()


    def openfile(self):
         fileName = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                 QtCore.QDir.currentPath())
         if fileName:
             image = QtGui.QImage(fileName)
             if image.isNull():
                 QtGui.QMessageBox.information(self, "Image Viewer",
                     "Cannot load %s." % fileName)
                 return

             self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
             self.scaleFactor = 1.0

             if not self.fitToWindowActive:
                 self.imageLabel.adjustSize()

    def emptyimage(self):
        # TODO: change this hardcoded size business ! Not even sure whether this is working for images that are not 512,512
        self.imageLabel.setPixmap(QtGui.QPixmap(QtCore.QSize(512,512)))
        self.scaleFactor = 1.0

        if not self.fitToWindowActive:
            self.imageLabel.adjustSize()
        self.scaleImage(1.0)

    def print_(self):
        dialog = QtGui.QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QtGui.QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        self.fitToWindowActive = not self.fitToWindowActive
        self.scrollArea.setWidgetResizable(self.fitToWindowActive)
        if not self.fitToWindowActive:
            self.normalSize()

    def createkeyboardshortcuts(self):
        self.shortcutZI = QtGui.QShortcut('+', self, self.zoomIn)
        self.shortcutZO = QtGui.QShortcut('-', self, self.zoomOut)
        self.shortcutNS = QtGui.QShortcut('=', self, self.normalSize)
        self.shortcutPrint = QtGui.QShortcut('p', self, self.print_)
        self.shortcutFit = QtGui.QShortcut('f', self, self.fitToWindow)

    def scaleImage(self, factor):
        previousvalue = self.scaleFactor
        self.scaleFactor *= factor
        # keep zoom within reasonable limits
        if self.scaleFactor < 0.25:
            self.scaleFactor = 0.25
        if self.scaleFactor > 4.0:
            self.scaleFactor = 4.0
        # in case we clipped the scaleFactor above we need to
        # calculate the actual scaling factor for the scrollbars
        actualfactor= self.scaleFactor/previousvalue
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), actualfactor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), actualfactor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
