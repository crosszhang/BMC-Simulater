#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""""
========================================================================================================
==                           Bmc UI - An UI for BMC Simulator                                         ==
==                                         Create by Sleepy (SESA480732)                              ==
==                                                                                                    ==
==                1.The FW, HW, SN, SKU MUST be set before you check "Online Status",                 ==
==                  and program will send them when you check "Online Status"                         ==
==                2.Wrong or Empty SKU setting may cause the DD not update correctly.                 ==
==                3.You should click 'OK' to send the temperature updates.                            ==
==                4.Other update will post automatically after you changed it.                        ==
==   As per the limitation of the interface, battery type and temperature will send the whole string  ==
=========================================================================================================
"""""


import sys
import traceback
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, \
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QCheckBox, QComboBox, QLabel, QSizePolicy, QTabWidget, \
    QDialog, QMessageBox, QDialogButtonBox


def import_bmc_node():
    try:
        bmc_node = __import__('BmcNode')
    except ImportError:
        bmc_node = None
    return bmc_node





CARTRIDGE_TYPES = [
    "E_NOT_PRESENT",
    "E_LCR127_R2_P1",
    "E_RESERVED1",
    "E_BP712",
    "E_RESERVED2",
    "E_CP1270",
    "E_RESERVED3",
    "E_GP1272",
    "E_RESERVED4",
    "E_PXL12090",
    "E_RESERVED5",
    "E_RESERVED6",
    "E_CP1290",
    "E_RESERVED7",
    "E_RESERVED8",
    "E_HR1234_WF2",
    "E_INVALID_TYPE",
]

CABINET_SKU = [
    'GVSMODBC6',
    'GVSMODBC6B',
    'GVSMODBC9',
    'GVSMODBC9B',
]


class BMCPanel(QWidget):
    LED_STATUS_STRING = ['X', '亮', '灭', '闪']

    def __init__(self, index: int, can_node, can_device):
        super().__init__()

        self.__index = index
        self.__can_node = can_node
        self.__can_device = can_device

        if self.__can_node is not None and self.__can_device is not None:
            self.__bmc_node = self.__can_node.BmcNode(self.__index, self.__can_device)
        else:
            self.__bmc_node = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(500)

        self.__label_led = QLabel('灭 灭 灭 灭 灭 灭 灭 灭 灭 灭')

        self.__edit_hw = QLineEdit('1.2.3')
        self.__edit_fw = QLineEdit('4.5.6.7')
        self.__edit_sn = QLineEdit('SN0123456789ABCD')
        self.__edit_mbc_sn = QLineEdit('SN-EXTERNAL-MBC1')
        self.__combox_sku = QComboBox()

        self.__check_bmc_status = QCheckBox('Online Status')
        self.__check_fuse1_status = QCheckBox('Fuse1 Status')
        self.__check_fuse2_status = QCheckBox('Fuse2 Status')
        self.__check_breaker_status = QCheckBox('Breaker Status')

        self.__check_bmc_present = QCheckBox('BMC Present')
        self.__check_fuse1_present = QCheckBox('Fuse1 Present')
        self.__check_fuse2_present = QCheckBox('Fuse2 Present')
        self.__check_breaker_present = QCheckBox('Breaker Present')

        self.__combox_device_type = [[None for cartridge_index in range(0, 4)] for string_index in range(0, 10)]
        self.__editor_device_temp = [[None for cartridge_index in range(0, 4)] for string_index in range(0, 10)]

        self.__init_ui()

    def __init_ui(self):
        self.__main_layout = QGridLayout()
        row = 0

        label = QLabel('Internal BMC' if self.__index == 0 else 'MBC' + str(self.__index))
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__main_layout.addWidget(label, row, 0)
        row += 1

        sub_layout = QHBoxLayout()
        label = QLabel('HW :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__edit_hw)
        self.__main_layout.addLayout(sub_layout, row, 0, 1, 2)

        sub_layout = QHBoxLayout()
        label = QLabel('FW :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__edit_fw)
        self.__main_layout.addLayout(sub_layout, row, 2, 1, 2)

        row += 1

        sub_layout = QHBoxLayout()
        label = QLabel('SN :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__edit_sn)
        self.__main_layout.addLayout(sub_layout, row, 0, 1, 2)

        sub_layout = QHBoxLayout()
        label = QLabel('SKU :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__combox_sku)
        self.__main_layout.addLayout(sub_layout, row, 2, 1, 2)

        row += 1

        sub_layout = QHBoxLayout()
        label = QLabel('MBC Serial Number :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__edit_mbc_sn, 1)
        label = QLabel('String LED :')
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(label)
        sub_layout.addWidget(self.__label_led, 1)
        row += 1

        self.__main_layout.addLayout(sub_layout, row, 0, 1, 4)

        row += 1

        self.__combox_sku.setEditable(True)
        for sku in CABINET_SKU:
            self.__combox_sku.addItem(sku)

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.__check_bmc_status)
        sub_layout.addWidget(self.__check_bmc_present)
        self.__main_layout.addLayout(sub_layout, row, 0)

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.__check_fuse1_status)
        sub_layout.addWidget(self.__check_fuse1_present)
        self.__main_layout.addLayout(sub_layout, row, 1)

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.__check_fuse2_status)
        sub_layout.addWidget(self.__check_fuse2_present)
        self.__main_layout.addLayout(sub_layout, row, 2)

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.__check_breaker_status)
        sub_layout.addWidget(self.__check_breaker_present)
        self.__main_layout.addLayout(sub_layout, row, 3)

        row += 1

        for string_index in range(0, 10):
            for cartridge_index in range(0, 4):
                temp_edit = QLineEdit()
                temp_edit.setText('25.0')
                temp_send = QPushButton("OK")
                temp_send.clicked.connect(
                    partial(self.on_btn_temperature_send, temp_edit, string_index, cartridge_index))
                tiny_layout = QHBoxLayout()
                tiny_layout.addWidget(temp_edit)
                tiny_layout.addWidget(temp_send)

                type_combox = QComboBox()
                type_combox.setEditable(False)
                for cartridge_type in CARTRIDGE_TYPES:
                    index = type_combox.count()
                    type_combox.addItem(cartridge_type + ' (' + str(index) + ')')
                    type_combox.setItemData(index, index)
                type_combox.setCurrentIndex(0)
                type_combox.currentIndexChanged.connect(
                    partial(self.on_cartridge_sel_changed, type_combox, string_index, cartridge_index))

                sub_layout = QVBoxLayout()
                sub_layout.addWidget(type_combox)
                sub_layout.addLayout(tiny_layout)

                self.__main_layout.addLayout(sub_layout, row + string_index, cartridge_index)
                self.__editor_device_temp[string_index][cartridge_index] = temp_edit
                self.__combox_device_type[string_index][cartridge_index] = type_combox
            row += 1

        self.__check_bmc_status.setChecked(False)
        self.__check_fuse1_status.setChecked(True)
        self.__check_fuse2_status.setChecked(True)
        self.__check_breaker_status.setChecked(True)

        self.__check_bmc_present.setChecked(True)
        self.__check_fuse1_present.setChecked(True)
        self.__check_fuse2_present.setChecked(True)
        self.__check_breaker_present.setChecked(True)

        self.__check_bmc_status.clicked.connect(partial(self.on_item_checked, self.__check_bmc_status, 'bmc_online'))
        self.__check_fuse1_status.clicked.connect(partial(self.on_item_checked, self.__check_fuse1_status, 'fuse1_status'))
        self.__check_fuse2_status.clicked.connect(partial(self.on_item_checked, self.__check_fuse2_status, 'fuse2_status'))
        self.__check_breaker_status.clicked.connect(partial(self.on_item_checked, self.__check_breaker_status, 'breaker_status'))

        self.__check_bmc_present.clicked.connect(partial(self.on_item_checked, self.__check_bmc_present, 'bmc_present'))
        self.__check_fuse1_present.clicked.connect(partial(self.on_item_checked, self.__check_fuse1_present, 'fuse1_present'))
        self.__check_fuse2_present.clicked.connect(partial(self.on_item_checked, self.__check_fuse2_present, 'fuse2_present'))
        self.__check_breaker_present.clicked.connect(partial(self.on_item_checked, self.__check_breaker_present, 'breaker_present'))

        self.setLayout(self.__main_layout)

    def on_timer(self):
        if self.__bmc_node is not None:
            led_status = self.__bmc_node.get_string_led_status()
            led_text = ' '.join([BMCPanel.LED_STATUS_STRING[status] for status in led_status])
            self.__label_led.setText(led_text)

    def on_item_checked(self, ctrl, id: str):
        checked = ctrl.isChecked()
        print('Check (' + ctrl.text() + ') ' + id + ' -> ' + str(checked))
        if self.__bmc_node is None:
            return

        if id == 'bmc_online':
            if checked:
                self.flush_data()
                self.__bmc_node.start()
            else:
                self.__bmc_node.stop()
        elif id == 'fuse1_status':
            self.__bmc_node.set_fuse(0, checked)
        elif id == 'fuse2_status':
            self.__bmc_node.set_fuse(1, checked)
        elif id == 'breaker_status':
            self.__bmc_node.set_breaker(checked)

        elif id == 'bmc_present':
            pass
        elif id == 'fuse1_present':
            pass
        elif id == 'fuse2_present':
            pass
        elif id == 'breaker_present':
            pass

    def on_cartridge_sel_changed(self, ctrl, string_index, cartridge_index):
        cartridge_type = ctrl.currentText()
        cartridge_enum = ctrl.currentData()
        print('on_cartridge_sel_changed ' + self.indicate_string(self.__index, string_index, cartridge_index))
        if self.__bmc_node is None:
            return
        if string_index < 0 or string_index >= len(self.__combox_device_type):
            return
        self.send_type(string_index)

    def on_btn_temperature_send(self, ctrl, string_index, cartridge_index):
        print('on_btn_temperature_send ' + self.indicate_string(self.__index, string_index, cartridge_index))
        if self.__bmc_node is None:
            return
        if string_index < 0 or string_index >= len(self.__editor_device_temp):
            return
        self.send_temperature(string_index)

    def flush_data(self):
        self.send_info()
        for string_index in range(0, 10):
            self.send_type(string_index)
            self.send_temperature(string_index)

        checked = self.__check_bmc_status.isChecked()
        if checked:
            self.__bmc_node.start()
        else:
            self.__bmc_node.stop()

        checked = self.__check_fuse1_status.isChecked()
        self.__bmc_node.set_fuse(0, checked)

        checked = self.__check_fuse2_status.isChecked()
        self.__bmc_node.set_fuse(1, checked)

        checked = self.__check_breaker_status.isChecked()
        self.__bmc_node.set_breaker(checked)

    def send_info(self):
        hw = self.__edit_hw.text()
        fw = self.__edit_fw.text()
        sn = self.__edit_sn.text()
        sku = self.__combox_sku.currentText()
        mbc_sn = self.__edit_mbc_sn.text()
        self.__bmc_node.config(hw=hw, fw=fw, sn=sn, sku=sku, mbc_sn=mbc_sn)

    def send_type(self, string_index):
        print('Set Type ' + self.indicate_string(self.__index, string_index, 'x') +
              str(self.__combox_device_type[string_index][0].currentData()) + ', ' +
              str(self.__combox_device_type[string_index][1].currentData()) + ', ' +
              str(self.__combox_device_type[string_index][2].currentData()) + ', ' +
              str(self.__combox_device_type[string_index][3].currentData())
              )
        try:
            self.__bmc_node.set_type(string_index,
                                     self.__combox_device_type[string_index][0].currentData(),
                                     self.__combox_device_type[string_index][1].currentData(),
                                     self.__combox_device_type[string_index][2].currentData(),
                                     self.__combox_device_type[string_index][3].currentData()
                                     )
        except Exception as e:
            print('String out of setting - Not send.')

    def send_temperature(self, string_index):
        print('Set temperature' + self.indicate_string(self.__index, string_index, 'x') +
              str(int(float(self.__editor_device_temp[string_index][0].text()))) + ', ' +
              str(int(float(self.__editor_device_temp[string_index][1].text()))) + ', ' +
              str(int(float(self.__editor_device_temp[string_index][2].text()))) + ', ' +
              str(int(float(self.__editor_device_temp[string_index][3].text())))
              )
        try:
            self.__bmc_node.set_temperature(string_index,
                                            int(float(self.__editor_device_temp[string_index][0].text())),
                                            int(float(self.__editor_device_temp[string_index][1].text())),
                                            int(float(self.__editor_device_temp[string_index][2].text())),
                                            int(float(self.__editor_device_temp[string_index][3].text()))
                                            )
        except Exception as e:
            print('String out of setting - Not send.')

    def indicate_string(self, device_index, string_index, cartridge_index):
        return '(' + str(device_index) + ', ' + str(string_index) + ', ' + str(cartridge_index) + ')'


class BMCBoard(QTabWidget):
    def __init__(self, can_node, can_device):
        super().__init__()
        self.__can_node = can_node
        self.__can_device = can_device
        self.__bmc_panels = []
        self.__tab_widget = QTabWidget(self)
        # self.__layout_main = QHBoxLayout()
        self.__layout_main = QVBoxLayout()
        self.init_ui()

    def init_ui(self):
        for i in range(0, 6):
            bmc_panel = BMCPanel(i, self.__can_node, self.__can_device)
            bmc_panel.setVisible(True)
            title = "Internal BMC" if i == 0 else "MBC" + str(i)
            self.__bmc_panels.append(bmc_panel)
            self.__tab_widget.addTab(bmc_panel, title)
            # self.__layout_main.addWidget(bmc_panel)
        self.__layout_main.addWidget(self.__tab_widget)
        self.setLayout(self.__layout_main)


class BmcCommunicationSelectDlg(QDialog):
    def __init__(self,parent=None):
        super(QDialog, self).__init__(parent)
        self.__comm_type = 0
        self.__combox_comm = QComboBox()
        self.__edit_ip = QLineEdit('127.0.0.1')
        self.__edit_port = QLineEdit('8001')
        self.__layout_main = QGridLayout()
        self.init_ui()

    def init_ui(self):
        self.setModal(True)
        self.resize(200, 80)
        self.setWindowTitle('BMC simulator communication mode selection')

        buttonBox = QDialogButtonBox(parent=self)
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)  # 确定
        buttonBox.rejected.connect(self.reject)  # 取消

        self.__combox_comm.addItem('PCAN')
        self.__combox_comm.addItem('Socket')
        self.__combox_comm.setItemData(0, 0)
        self.__combox_comm.setItemData(1, 1)

        self.__layout_main.addWidget(QLabel('Mode: '), 0, 0)
        self.__layout_main.addWidget(self.__combox_comm, 0, 1)

        self.__layout_main.addWidget(QLabel('IP: '), 1, 0)
        self.__layout_main.addWidget(self.__edit_ip, 1, 1)

        self.__layout_main.addWidget(QLabel('Port: '), 2, 0)
        self.__layout_main.addWidget(self.__edit_port, 2, 1)

        self.__layout_main.addWidget(buttonBox, 3, 1)

        self.setLayout(self.__layout_main)

    def closeEvent(self, event):
        reply = QMessageBox().question(self, 'Close Message', "Are you sure to quit?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            exit(99999)
        else:
            event.ignore()

    def get_config(self):
        mode = self.__combox_comm.currentData()
        return mode, self.__edit_ip.text(), self.__edit_port.text()


class BmcMainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.__mode = 0
        self.bmc_node = None
        self.can_device = None

        comm_sel_dlg = BmcCommunicationSelectDlg(self)
        comm_sel_dlg.exec_()

        self.__mode, ip, port = comm_sel_dlg.get_config()

        try:
            self.bmc_node = __import__('BmcNode')
        except ImportError:
            print('=================================================================')
            print('Import BmcNode Failed. Please check whether can lib is installed.')
            print('                     pip install python-can                      ')
            print('=================================================================')
            exit(2333)

        try:
            if self.__mode == 0:
                self.can_device = self.bmc_node.CanDevice(0)
            else:
                self.can_device = self.bmc_node.SimCanDevice(ip, int(port))
                self.can_device.enable()
        except Exception as e:
            if self.__mode == 0:
                print('=================================================================')
                print('              The CAN device is not connected.')
                print('=================================================================')
            else:
                print('=================================================================')
                print('                   Wrong config for Socket')
                print('=================================================================')
            self.__mode = 0
            self.can_device = None
            # exit(6666)

        self.__bmc_board = BMCBoard(self.bmc_node, self.can_device)
        self.init_ui()

    def init_ui(self):
        self.setCentralWidget(self.__bmc_board)
        self.setMinimumSize(800, 700)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
        self.setWindowTitle('BMC UI - Sleepy')

    def closeEvent(self, event):
        result = QMessageBox().question(self, "Confirm Exit...", "Are you sure you want to exit ?",
                                        QMessageBox.Yes | QMessageBox.No)
        event.ignore()

        if result == QMessageBox.Yes:
            if self.can_device is not None and self.__mode == 1:
                self.can_device.disable()
            event.accept()


def main():
    app = QApplication(sys.argv)
    main_wnd = BmcMainWindow()
    main_wnd.show()
    app.exec_()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = exception_hook


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
