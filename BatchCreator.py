import sys
import re
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QComboBox, QButtonGroup, QMessageBox, QRadioButton, QPushButton,
    QLabel, QStyle, QLineEdit,
    QTextEdit, QFrame)
from PySide6.QtCore import Qt, QThread, QIODevice, QTextStream, Signal, Slot, QRect
from PySide6.QtGui import QIcon

from wwise_objects import *
from client import Client


class WorkThread(QThread):
    # waapi 已连接 信号
    waapi_connected = Signal(str)
    waapi_disconnected = Signal(str)
    waapi_selectionChanged = Signal(list)

    # 错误信号
    error_signal = Signal(str)

    # 接收主窗口的信号
    current_object_type_signal = Signal(str)
    name_list_signal = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self.current_object_type = None
        self.name_list = None
        self.parent_path_list = None
        self.last_created_list = []
        self.current_object_type_signal.connect(self.set_current_object_type)
        self.name_list_signal.connect(self.set_name_list)

    def try_connect(self):
        try:
            self.client = Client()
            self.client.on_selectionChanged(self.on_selectionChanged)
            self.waapi_connected.emit(self.client.version)
            self.waapi_selectionChanged.emit(self.get_parent_path_list())
        except Exception as e:
            self.waapi_disconnected.emit(str(e))

    def get_parent_path_list(self):
        # 先保存当前的选择，然后返回给主窗口显示
        self.parent_path_list = [
            i['path']for i in self.client.selected_object]
        return self.parent_path_list

    def on_selectionChanged(self, *args, **kwargs):
        # 回调函数，监听 waapi 的 selectionChanged 信号，更新 parent_path_list
        parent_path_list = kwargs.get('objects')
        self.parent_path_list = [
            i['path']for i in parent_path_list]
        self.waapi_selectionChanged.emit(self.parent_path_list)

    def set_current_object_type(self, object_type):
        self.current_object_type = object_type

    def set_name_list(self, name_list):
        self.name_list = name_list

    def delete_last_created(self):
        for _id in self.last_created_list:
            self.client.delete_object(_id)

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        if self.client and self.client.is_connected:
            self.client.disconnect()

    def run(self):
        print('WorkThread: run')
        checked_None = False
        None_list = []
        self.last_created_list = []
        for parent_path in self.parent_path_list:
            for name in self.name_list:
                result = self.client.create_object(
                    self.current_object_type, name, parent_path)
                if not result:
                    checked_None = True
                    None_list.append({
                        'type': self.current_object_type,
                        'name': name,
                        'parent': parent_path
                    })
                else:
                    self.last_created_list.append(result['id'])

        # 显示未成功创建对象的名称和路径
        if checked_None:
            error_text = json.dumps(None_list[:5] if len(
                None_list) >= 5 else None_list, ensure_ascii=False, indent=4)
            self.error_signal.emit(
                'Some objects are not created!\n' +
                error_text +
                ('\n......    More failures are logged in the log file'
                 if len(None_list) >= 5 else ''))
            # 记录到日志文件
            self.client.log(error_text)


class MainWindow(QWidget):

    # 状态栏信号
    status_bar_signal = Signal(str)
    # 当前选中的按钮信号
    current_btn_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.selection = []
        self.setWindowTitle('Wwise Object Creator - disconnected')
        # 置顶窗口
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.workThread = WorkThread()
        self.createTitleBar()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        # 测试连接waapi，连接失败会禁用窗口控件
        self.workThread.try_connect()

    def createTitleBar(self):
        # 本来想做自定义标题栏的，有点麻烦，放弃了
        self.titleBarLayout = QHBoxLayout()
        self.titleBarLayout.setContentsMargins(0, 0, 0, 0)
        self.titleBarLayout.setSpacing(0)
        self.titleBar = QFrame()
        self.titleBar.setObjectName('titleBar')
        self.titleBar.setFixedHeight(30)
        self.title = QLabel('Wwise Object Creator')
        self.closeBtn = QPushButton(self.titleBar)
        # 去边框
        self.closeBtn.setStyleSheet('border: none;')
        # 设置自带关闭图标
        self.closeBtn.setIcon(self.style().standardIcon(
            QStyle.SP_TitleBarCloseButton))
        self.titleBarLayout.addWidget(self.titleBar)

    def createWidgets(self):
        self.label_1 = QLabel('Create type:')
        self.label_2 = QLabel('Selected parent path:')
        self.label_3 = QLabel('Name list edit:')

        self.selectedPathEdit = QLineEdit()
        self.selectedPathEdit.setReadOnly(True)
        self.textEdit = QTextEdit()
        self.createBtn = QPushButton('Create')
        self.createBtn.setStyleSheet(
            'background-color: dimgray; font-size:20px;')
        self.btnGroup = QButtonGroup()

        self.btnGroupLayout = QHBoxLayout()
        self.btnGroupLayout.setAlignment(Qt.AlignLeft)
        for _data in WWISE_OBJECT_TABLE['Audio']:
            icon_path = _data['icon_path']
            # dis_icon_pth = icon_path[:].replace('_nor', '_dis')
            waapi_name = _data['waapi_name']
            display_name = _data['display_name']

            radioBtn = QRadioButton()
            radioBtn.setIcon(QIcon(icon_path))
            radioBtn.setToolTip(f'Select {display_name}')
            radioBtn.setObjectName(waapi_name)
            radioBtn.setProperty('display_name', display_name)
            radioBtn.setProperty('waapi_name', waapi_name)

            radioBtn.toggled.connect(self.on_radio_btn_toggled)
            self.btnGroup.addButton(radioBtn)
            self.btnGroupLayout.addWidget(radioBtn)

        # 默认选中第一个按钮
        self.btnGroup.buttons()[0].setChecked(True)

        # 测试用按钮
        self.testDeleteBtn = QPushButton('Delete last created')
        self.testDeleteBtn.setStyleSheet(
            'background-color: dimgray; font-size:20px;')
        self.testDeleteBtn.clicked.connect(self.workThread.delete_last_created)

    def createLayouts(self):
        layout = QVBoxLayout()
        # layout.addLayout(self.titleBarLayout)
        layout.addWidget(self.label_1)
        layout.addLayout(self.btnGroupLayout)
        layout.addWidget(self.label_2)
        layout.addWidget(self.selectedPathEdit)
        layout.addWidget(self.label_3)
        layout.addWidget(self.textEdit)
        layout.addSpacing(20)
        layout.addWidget(self.createBtn)
        layout.addSpacing(20)
        # 添加测试按钮
        layout.addWidget(self.testDeleteBtn)
        self.setLayout(layout)

    def createConnections(self):
        self.createBtn.clicked.connect(self.on_create_btn_clicked)
        self.workThread.waapi_connected.connect(self.on_connected)
        self.workThread.waapi_disconnected.connect(self.on_disconnected)
        self.workThread.waapi_selectionChanged.connect(
            self.on_selectionChanged)
        # 创建对象失败的信号
        self.workThread.error_signal.connect(
            lambda msg: QMessageBox.warning(self, 'Warning', msg))

    def on_radio_btn_toggled(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet(
                '*{background-color: dimgray;}\nQToolTip {border: none;background-color: dimgray;}')
            self.createBtn.setText(f'Create {sender.property("display_name")}')
            # 发送当前选中的按钮信号
            self.workThread.current_object_type_signal.emit(
                sender.property('waapi_name'))
        else:
            sender.setStyleSheet(
                '*{background-color: transparent;}\nQToolTip {border: none;background-color: dimgray;}')

    def on_selectionChanged(self, parent_path_list):
        parent_path_list

        # 更新lienEdit
        self.selectedPathEdit.setText(
            json.dumps(parent_path_list, ensure_ascii=False))

        # 鼠标悬停lineEdit 显示选择对象路径列表
        self.selectedPathEdit.setToolTip(json.dumps(
            parent_path_list, ensure_ascii=False, indent=4))

    def on_create_btn_clicked(self):
        text = self.textEdit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, 'Error', 'Please input name list')
            return

        name_list = []
        for line in text.splitlines():
            name = line.strip()
            if name:
                name_list.append(name)

        # 发送当前输入框名字列表信号
        self.workThread.name_list_signal.emit(name_list)

        # 启动线程
        self.workThread.start()

    def on_connected(self, version):
        self.setWindowTitle(f'Wwise Object Creator - Connected Wwise{version}')

    def on_disconnected(self, error):
        self.setWindowTitle('Wwise Object Creator - disconnected')
        QMessageBox.information(self, 'Error', error)
        self.setDisabled(True)

    def closeEvent(self, event) -> None:
        self.workThread.disconnect()
        self.workThread.quit()
        return super().closeEvent(event)


STYLE = """
* {
    background-color: rgb(58,58,58);
    color: rgb(201,201,201);
}
QToolTip {
    border: none;
    background-color: dimgray;
    color: rgb(201,201,201);
    font-size: 14px;
}
"""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setStyleSheet(STYLE)
    window.show()
    sys.exit(app.exec())
