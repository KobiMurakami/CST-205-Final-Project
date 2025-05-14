## Kobi Murakami
## CST 205 Final Project
## Solo Project
## 5-13-25
## App that allows you to upload and edit images and save them to your computer

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QComboBox, QLineEdit, QSpinBox, QFormLayout, QGroupBox, QSizePolicy, QSpacerItem,
    QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QImage
from PIL import Image, ImageOps
import io

class ImageProcessingThreads(QObject):
    progress = Signal(int)
    finished = Signal(Image.Image)

    ##This block is setting up threads which allows the progress bars to work
    ##It puts the slow image processing function on a background thread
    ##Then puts the progress bar on the main one

    def __init__(self, image, operation, color_modifiers=None):
        super().__init__()
        self.image = image
        self.operation = operation
        self.color_modifiers = color_modifiers

    def run(self):
        width, height = self.image.size
        total_pixels = width * height
        newImage = Image.new("RGB", (width, height))
        pixels = self.image.load()

        if self.operation == 'sepia':
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    newImage.putpixel((x, y), (min(tr, 255), min(tg, 255), min(tb, 255)))
                self.progress.emit(int(((y+1) * width) / total_pixels * 100))

        elif self.operation == 'rgb':
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    r = min(int(r * self.color_modifiers['r']), 255)
                    g = min(int(g * self.color_modifiers['g']), 255)
                    b = min(int(b * self.color_modifiers['b']), 255)
                    newImage.putpixel((x, y), (r, g, b))
                self.progress.emit(int(((y+1) * width) / total_pixels * 100))

        elif self.operation == 'negative':
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    newImage.putpixel((x, y), (255 - r, 255 - g, 255 - b))
                self.progress.emit(int(((y+1) * width) / total_pixels * 100))

        self.finished.emit(newImage)


class ImageEditor(QWidget):
    def __init__(self):
        super().__init__()

        ##This block is just setting up the GUI with buttons and layout features

        self.setWindowTitle("Image Editor")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #51967a;")
        mainLayout = QHBoxLayout(self)

        leftColumn = QWidget()
        leftColumn.setFixedWidth(320)
        leftColumn.setStyleSheet("background-color: #d3d3d3;")
        leftLayout = QVBoxLayout(leftColumn)
        leftLayout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        leftLayout.setSpacing(8)

        self.imageLabel = QLabel("Upload an Image")
        self.imageLabel.setFixedSize(700, 700)
        self.imageLabel.setStyleSheet("border: 1px solid black; background-color: white;")
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.originalImage = None
        self.editedImage = None

        def makeButton(text):
            btn = QPushButton(text)
            btn.setFixedSize(200, 40)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            return btn

        self.controlsPanel = QFormLayout()

        self.greyBtn = makeButton("Greyscale")
        self.greyBtn.clicked.connect(self.applyGreyscale)
        self.controlsPanel.addRow(self.centerWidget(self.greyBtn))

        self.sepiaBtn = makeButton("Sepia")
        self.sepiaBtn.clicked.connect(self.applySepia)
        self.controlsPanel.addRow(self.centerWidget(self.sepiaBtn))

        self.negativeBtn = makeButton("Negative")
        self.negativeBtn.clicked.connect(self.applyNegative)
        self.controlsPanel.addRow(self.centerWidget(self.negativeBtn))

        self.widthSpin = QSpinBox()
        self.widthSpin.setRange(50, 3000)
        self.widthSpin.setFixedWidth(200)
        self.widthSpin.setStyleSheet("background-color: white;")
        self.widthSpin.valueChanged.connect(self.updateImageDisplay)

        self.heightSpin = QSpinBox()
        self.heightSpin.setRange(50, 3000)
        self.heightSpin.setFixedWidth(200)
        self.heightSpin.setStyleSheet("background-color: white;")
        self.heightSpin.valueChanged.connect(self.updateImageDisplay)

        self.controlsPanel.addRow("Width:", self.centerWidget(self.widthSpin))
        self.controlsPanel.addRow("Height:", self.centerWidget(self.heightSpin))

        self.rInput = QLineEdit("100")
        self.rInput.setFixedWidth(100)
        self.rInput.setStyleSheet("background-color: white;")
        self.rApply = QPushButton("Apply")
        self.rApply.setFixedWidth(60)
        self.rApply.clicked.connect(lambda: self.applyRgb())

        self.gInput = QLineEdit("100")
        self.gInput.setFixedWidth(100)
        self.gInput.setStyleSheet("background-color: white;")
        self.gApply = QPushButton("Apply")
        self.gApply.setFixedWidth(60)
        self.gApply.clicked.connect(lambda: self.applyRgb())

        self.bInput = QLineEdit("100")
        self.bInput.setFixedWidth(100)
        self.bInput.setStyleSheet("background-color: white;")
        self.bApply = QPushButton("Apply")
        self.bApply.setFixedWidth(60)
        self.bApply.clicked.connect(lambda: self.applyRgb())

        self.controlsPanel.addRow("Red (%):", self.createRgbRow(self.rInput, self.rApply))
        self.controlsPanel.addRow("Green (%):", self.createRgbRow(self.gInput, self.gApply))
        self.controlsPanel.addRow("Blue (%):", self.createRgbRow(self.bInput, self.bApply))

        resetBtn = makeButton("Reset Image")
        resetBtn.clicked.connect(self.resetImage)
        self.controlsPanel.addRow(self.centerWidget(resetBtn))

        controlsGroup = QGroupBox("Image Controls")
        controlsGroup.setLayout(self.controlsPanel)
        leftLayout.addWidget(controlsGroup)
        leftLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        fileButtonsLayout = QVBoxLayout()
        fileButtonsLayout.setAlignment(Qt.AlignCenter)

        uploadBtn = makeButton("Upload Image")
        uploadBtn.clicked.connect(self.uploadImage)

        saveBtn = makeButton("Save Image")
        saveBtn.clicked.connect(self.saveImage)

        fileButtonsLayout.addWidget(uploadBtn)
        fileButtonsLayout.addWidget(saveBtn)

        fileGroup = QGroupBox("File Actions")
        fileGroup.setLayout(fileButtonsLayout)
        fileGroup.setAlignment(Qt.AlignCenter)
        leftLayout.addWidget(fileGroup)

        mainLayout.addWidget(leftColumn, alignment=Qt.AlignLeft)
        mainLayout.addWidget(self.imageLabel, alignment=Qt.AlignCenter)

        self.colorModifiers = {'r': 1.0, 'g': 1.0, 'b': 1.0}

    def centerWidget(self, widget):
        wrapper = QWidget()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(widget)
        wrapper.setLayout(layout)
        return wrapper

    def createRgbRow(self, inputField, applyButton):
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        row.addWidget(inputField)
        row.addWidget(applyButton)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def showProgressDialog(self, title):
        dlg = QProgressDialog(title, "Cancel", 0, 100, self)
        dlg.setWindowTitle(title)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        return dlg
    
    ##All functions below here are for image processing and image displays.
    ##runImageProcessing is the function that creates the threads and runs the
    ##Processes in the background

    def runImageProcessing(self, operation, color_modifiers=None):
        if not self.originalImage:
            return
        dlg = self.showProgressDialog(f"Applying {operation.title()}...")
        self.thread = QThread()
        self.worker = ImageProcessingThreads(self.originalImage.copy(), operation, color_modifiers)
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(dlg.setValue)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        def on_finish(image):
            self.editedImage = image
            self.updateImageDisplay()
            self.resetRgbInputs()
            dlg.close()

        self.worker.finished.connect(on_finish)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def uploadImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if fileName:
            self.originalImage = Image.open(fileName).convert("RGB")
            self.editedImage = self.originalImage.copy()
            w, h = self.originalImage.size
            self.widthSpin.setValue(w)
            self.heightSpin.setValue(h)
            self.updateImageDisplay()

    def updateImageDisplay(self):
        if not self.editedImage:
            return
        resized = self.editedImage.resize((self.widthSpin.value(), self.heightSpin.value()))
        data = io.BytesIO()
        resized.save(data, format="PNG")
        qimg = QImage.fromData(data.getvalue())
        self.imageLabel.setPixmap(QPixmap.fromImage(qimg))

    def applyGreyscale(self):
        if self.editedImage:
            self.editedImage = ImageOps.grayscale(self.editedImage).convert("RGB")
            self.resetRgbInputs()
            self.updateImageDisplay()

    def applySepia(self):
        self.runImageProcessing('sepia')

    def applyNegative(self):
        self.runImageProcessing('negative')

    def applyRgb(self):
        if not self.originalImage:
            return
        try:
            rVal = float(self.rInput.text()) / 100
            gVal = float(self.gInput.text()) / 100
            bVal = float(self.bInput.text()) / 100
        except ValueError:
            return
        self.colorModifiers = {'r': rVal, 'g': gVal, 'b': bVal}
        self.runImageProcessing('rgb', self.colorModifiers)

    def resetRgbInputs(self):
        self.rInput.setText("100")
        self.gInput.setText("100")
        self.bInput.setText("100")
        self.colorModifiers = {'r': 1.0, 'g': 1.0, 'b': 1.0}

    def resetImage(self):
        if self.originalImage:
            self.editedImage = self.originalImage.copy()
            w, h = self.originalImage.size
            self.widthSpin.setValue(w)
            self.heightSpin.setValue(h)
            self.resetRgbInputs()
            self.updateImageDisplay()

    def saveImage(self):
        if self.editedImage:
            fileName, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)")
            if fileName:
                resized = self.editedImage.resize((self.widthSpin.value(), self.heightSpin.value()))
                resized.save(fileName)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.exit(app.exec())
