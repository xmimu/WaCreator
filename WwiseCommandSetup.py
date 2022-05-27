import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QButtonGroup, QCheckBox, QRadioButton, QLineEdit, QFrame
from PySide6.QtCore import Slot, QFile, QIODevice, QTextStream, Signal, QRect, Qt
from PySide6.QtGui import QIcon

settings = {
    "version": 2,
    "commands": [
        {
            "id": "my.bnc_tools",
            "displayName": "BNC_Tools",
            "program": "",
            "cwd": "",
            "args": "",
            "contextMenu": {
                "visibleFor": "Sound"
            },
            "mainMenu": {
                "basePath": "BNC_Tools"
            }
        }
    ]
}


class Window(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Wwise Command Setup")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        for k, v in settings['commands'][0].items():
            label = QLabel(f'{k}:')
            lineEdit = QLineEdit(str(v))
            layout.addWidget(label)
            layout.addWidget(lineEdit)
            setattr(self, f'{k}_edit', lineEdit)

        self.btn = QPushButton('Create')
        # 设置间隔距离
        layout.addSpacing(30)
        layout.addWidget(self.btn)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
