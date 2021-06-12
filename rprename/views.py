# -*- coding: utf-8 -*-
# rprename/views.py

"""This module provides the RP Renamer main window."""

from collections import deque
from pathlib import Path

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QWidget, QFileDialog

from .rename import Renamer
from .ui.window import Ui_Window

FILTERS = ";;".join(
    (
        "PNG Files (*.png)",
        "JPEG Files (*.jpeg)",
        "JPG Files (*.jpg)",
        "GIF Files (*.gif)",
        "Text Files (*.txt)",
        "Python Files (*.py)",
    )
)


class Window(QWidget, Ui_Window):
    def __init__(self):
        super().__init__()
        self._files = deque()
        self._filesCount = len(self._files)
        self._setupUI()
        self._updateStateWhenNoFiles()
        self._connectSignalsSlots()

    def _setupUI(self):
        self.setupUi(self)

    def _updateStateWhenNoFiles(self):
        self._filesCount = len(self._files)
        self.loadFilesButton.setEnabled(True)
        #self.loadFilesButton.setFocus(True)
        self.remaneFilesButton.setEnabled(False)
        self.prefixEdit.clear()
        self.prefixEdit.setEnabled(False)

    def _connectSignalsSlots(self):
        self.loadFilesButton.clicked.connect(self.loadFiles)
        self.remaneFilesButton.clicked.connect(self.renameFiles)

    def renameFiles(self):
        self._runRenamerThread()

    def _runRenamerThread(self):
        prefix = self.prefixEdit.text()
        self._thread = QThread()
        self._renamer = Renamer(
            files=tuple(self._files),
            prefix=prefix
        )

        self._renamer.moveToThread(self._thread)
        self._thread.started.connect(self._renamer.renameFiles)
        self._renamer.renamedFile.connect(self._updateStateWhenFileRenamed)
        self._renamer.progressed.connect(self._updateProgressBar)
        self._renamer.finished.connect(self._thread.quit)
        self._renamer.finished.connect(self._renamer.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._renamer.finished.connect(self._updateStateWhenNoFiles)
        self._thread.start()

    def _updateStateWhenFileRenamed(self, newFile):
        self._files.popleft()
        self.srcFileList.takeItem(0)
        self.dstFileList.addItem(str(newFile))


    def _updateProgressBar(self, file_number):
        progressPercent = int(file_number / self._filesCount * 100)
        self.progressBar.setValue(progressPercent)


    def loadFiles(self):
        self.dstFileList.clear()
        if self.dirEdit.text():
            initDir = self.dirEdit.text()
        else:
            initDir = str(Path.home())

        files, filter = QFileDialog.getOpenFileNames(
            self,
            "Choose File to Rename",
            initDir,
            filter=FILTERS
        )

        if len(files) <= 0:
            return

        fileExtension = filter[filter.index("*"):-1]
        self.extensionLable.setText(fileExtension)
        srcDirName = str(Path(files[0]).parent)
        self.dirEdit.setText(srcDirName)
        for file in files:
            self._files.append(Path(file))
            self.srcFileList.addItem(file)
        self._filesCount = len(self._files)
        self._updateStateWhenFilesLoaded()


    def _updateStateWhenFilesLoaded(self):
        self.prefixEdit.setEnabled(True)
        self.remaneFilesButton.setEnabled(True)