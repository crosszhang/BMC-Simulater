import can
import sys
import threading
import queue
import time
import socket
from abc import ABCMeta, abstractmethod


class Node:
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def on_message(self, msg_id: int, msg_data: bytearray):
        pass

    __metaclass__ = ABCMeta
    pass


class Device:
    def __init__(self):
        self.__nodes = {}
        self.__lock = threading.Lock()
        pass

    def add_node(self, index: int, node: Node):
        if index < 0 or index > 9:
            _error_msg = '{} out of the rage of index that is 0 ~ 9'.format(index)
            raise ValueError(_error_msg)
            pass
        with self.__lock:
            self.__nodes[index] = node
        pass

    def on_message(self, msg):
        # print(msg)
        # max supports 10 BMCs and index range is 0 ~ 9
        _index = (msg.arbitration_id >> 24) & 0xf
        if _index == 0xa:
            _index = 0
            pass
        elif _index < 1 or _index > 0xa:
            _index = None
            pass
        else:
            pass
        try:
            with self.__lock:
                _node = self.__nodes[_index]
            _node.on_message(msg.arbitration_id & 0xffff, msg.data)
            pass
        except KeyError:
            pass
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    @abstractmethod
    def send_message(self, msg):
        pass

    __metaclass__ = ABCMeta
    pass


class _CanListener(can.listener.Listener):
    def __init__(self, device: Device):
        self.__dev = device
        pass

    def on_message_received(self, msg):
        self.__dev.on_message(msg)
        pass

    pass


class CanDevice(Device):
    def __init__(self, device_index: int = 0):
        super(CanDevice, self).__init__()
        if sys.platform == 'linux':
            # sudo ip link set can0 up type can bitrate 500000
            self.__channel = 'can{}'.format(device_index)
            self.__bus_type = 'socketcan'
            pass
        else:
            self.__channel = 'PCAN_USBBUS{}'.format(device_index + 1)
            self.__bus_type = 'pcan'
            pass
        self.__can_bus_instance = None
        self.__listener = None
        self.__can_notifier = None
        self.enable()

    @property
    def __can_bus(self):
        if self.__can_bus_instance is None:
            raise IOError('Can device is not enabled')
        else:
            return self.__can_bus_instance
        pass

    def send_message(self, msg: can.Message):
        for _i in range(11):
            try:
                self.__can_bus.send(msg)
                break
                pass
            except can.CanError as _e:
                if _i < 10:
                    time.sleep(0.1)
                    pass
                else:
                    raise _e
                pass
            pass
        pass

    def enable(self):
        if self.__can_bus_instance is None:
            self.__can_bus_instance = can.interface.Bus(channel=self.__channel,
                                                        bustype=self.__bus_type,
                                                        bitrate=500000)
            self.__listener = _CanListener(self)
            self.__can_notifier = can.Notifier(bus=self.__can_bus, listeners=[self.__listener, ])
            pass
        else:
            pass
        pass

    def disable(self):
        if self.__can_bus_instance is None:
            pass
        else:
            self.__listener.stop()
            self.__can_notifier.stop()
            self.__can_bus.shutdown()
            self.__can_bus_instance = None
            self.__listener = None
            self.__can_notifier = None
            pass
        pass

    pass


if sys.platform == 'linux':
    from can.interfaces.socketcan.socketcan import build_can_frame, capture_message
    import select


    class SimCanDevice(Device):
        def __init__(self, ip: str, port: int):
            super(SimCanDevice, self).__init__()
            self.__remote = (ip, port)
            self.__local = ('0.0.0.0', 8002)
            self.__udp_socket = None
            self.__thread = None
            self.__terminal = False
            pass

        def enable(self):
            if self.__thread is None:
                self.__terminal = False
                self.__udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.__udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.__udp_socket.bind(self.__local)
                self.__thread = threading.Thread(target=self.__run)
                self.__thread.start()
                pass
            pass

        def disable(self):
            if isinstance(self.__thread, threading.Thread):
                if self.__thread.isAlive():
                    self.__terminal = True
                    self.__thread.join()
                    self.__udp_socket.close()
                    self.__thread = None
            pass

        def send_message(self, msg: can.Message):
            for _i in range(11):
                _data = build_can_frame(msg)
                _n_byte = self.__udp_socket.sendto(_data, self.__remote)
                if _n_byte == len(_data):
                    break
                    pass
                else:
                    if _i < 10:
                        time.sleep(0.1)
                        pass
                    else:
                        raise can.CanError("Transmit buffer full")
                pass
            pass

        def __run(self):
            print('SimCanDevice is enabled')
            while True:
                _ready = select.select([self.__udp_socket], [], [], 1)[0]
                if _ready:
                    _msg = capture_message(_ready[0], False)
                    self.on_message(_msg)
                    pass
                else:
                    pass

                if self.__terminal:
                    print('SimCanDevice is disabled')
                    break
                pass
            pass

        pass


    pass


class BmcNode(Node):
    E_BAT_TYPE_INVALID_TYPE = 0  # Invalid Type
    E_BAT_TYPE_LCR127R2P1 = 1  # Panasonic LCR127R2P1 7AH
    E_BAT_TYPE_RESERVED1 = 2  # Reserved battery type 1
    E_BAT_TYPE_BP712 = 3  # BB BP712 7AH
    E_BAT_TYPE_RESERVED2 = 4  # Reserved battery type 2
    E_BAT_TYPE_CP1270 = 5  # Vision CP1270 7AH
    E_BAT_TYPE_RESERVED3 = 6  # Reserved battery type 3
    E_BAT_TYPE_GP1272 = 7  # CSB GP1272 7AH
    E_BAT_TYPE_RESERVED4 = 8  # Reserved battery type 4
    E_BAT_TYPE_PXL12090 = 9  # Yuasa PXL12090 9AH
    E_BAT_TYPE_RESERVED5 = 10  # Reserved battery type 5
    E_BAT_TYPE_RESERVED6 = 11  # Reserved battery type 6
    E_BAT_TYPE_CP1290 = 12  # Vision CP1290 9AH
    E_BAT_TYPE_RESERVED7 = 13  # Reserved battery type 7
    E_BAT_TYPE_RESERVED8 = 14  # Reserved battery type 8
    E_BAT_TYPE_HR1234WF2 = 15  # CSB HR1234WF2 9AH
    E_BAT_TYPE_NOT_PRESENT = 16  # Not present

    E_BREAKER_OFF = False
    E_BREAKER_ON = True

    E_FUSE_BROKEN = False
    E_FUSE_NORMAL = True

    E_STRING_LED_ON = 1
    E_STRING_LED_OFF = 2
    E_STRING_LED_FLASH = 3

    def __init__(self, index: int, can_dev: Device):
        """
        :param index: range 0 ~ 15, 0 -> id: 0x1A, 1 -> id: 0x11, 2 -> id: 0x12 ...
                      0x1A is the internal BMC
                      0x11 is the external BMC1
                      0x12 is the external BMC2
                      ...
        :param can_dev: the can device instance
        """
        self.__can_dev = can_dev
        self.__index = index
        self.__can_dev.add_node(self.__index, self)
        self.__thread = None
        self.__msg_queue = queue.Queue()
        self.__run_state = False
        self.__battery_num = 10
        self.__string_led = [BmcNode.E_STRING_LED_OFF] * 10

        # BMC Static Data
        self.__sn = 'SN*************E'
        self.__fw = {
            'major': 0,
            'minor': 1,
            'deviation': 2,
            'build': 0x1234
        }
        self.__hw = {
            'build': 0,
            'version': 1,
            'config': 0x12345678
        }

        self.__sku = 'SKU************E'
        self.__mbc_sn = 'SN*MBC*********E'
        # BMC Dynamic Data
        self.__fuse = [False, True]
        self.__breaker = False
        self.__current = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.__bat_type = [
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00]
        ]
        self.__bat_temp = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]

        # Command Actions
        self.__cmd_actions = {
            0x0201: (self.__send_fw, False),
            0x0206: (self.__send_hw, False),
            0x0204: (self.__send_sn, False),
            0x0330: (self.__send_all_sample_data, False),
            0x0211: (self.__send_sku, False),
            0x0213: (self.__send_mbc_sn, False),
            0x032A: (self.__drive_led_1_6, True),
            0x032B: (self.__drive_led_7_10, True),
        }
        pass

    @property
    def fw(self):
        return '{}.{}.{}.{}'.format(self.__fw['major'],
                                    self.__fw['minor'],
                                    self.__fw['deviation'],
                                    self.__fw['build'])
        pass

    @property
    def hw(self):
        return '{}.{}.{}'.format(self.__hw['build'], self.__hw['version'], self.__hw['config'])
        pass

    @property
    def sn(self):
        return self.__sn
        pass

    @property
    def sku(self):
        return self.__sku
        pass

    @property
    def mbc_sn(self):
        return self.__mbc_sn
        pass

    @property
    def battery_number(self):
        return self.__battery_num
        pass

    @battery_number.setter
    def battery_number(self, value: int):
        if isinstance(value, int) and (value > -1 or value < 11):
            self.__battery_num = value
            pass
        else:
            raise ValueError('invalid battery number {}'.format(value))
        pass

    def send_message(self, msg_id: int, msg_data: bytearray = None):
        """
        :param msg_id: 16bit value, it is the id which is defined by BMC Can Protocol
        :param msg_data: message data
        :return:
        """
        _id = msg_id | (0x1a000000 if self.__index == 0 else ((self.__index << 24) | 0x10000000))
        _msg = can.message.Message(extended_id=True, arbitration_id=_id, data=msg_data)
        self.__msg_queue.put(_msg)
        pass

    def start(self):
        if self.__thread is None:
            self.__thread = threading.Thread(target=self._run)
            self.__thread.start()
            self.__run_state = True
            pass
        pass

    def stop(self):
        if isinstance(self.__thread, threading.Thread):
            if self.__thread.isAlive():
                self.__run_state = False
                self.__msg_queue.put(None)
                self.__thread.join()
                self.__thread = None
        pass

    def config(self, **kwargs):
        try:
            _fw = kwargs['fw']
            if isinstance(_fw, str):
                self.__parse_fw(_fw)
                pass
            else:
                raise TypeError('firmware version must be the string type')
            pass
        except KeyError:
            pass

        try:
            _hw = kwargs['hw']
            if isinstance(_hw, str):
                self.__parse_hw(_hw)
                pass
            else:
                raise TypeError('hardware version must be the string type')
            pass
        except KeyError:
            pass

        try:
            _sn = kwargs['sn']
            if isinstance(_sn, str):
                if len(_sn) <= 16:
                    self.__sn = _sn
                    pass
                else:
                    raise ValueError('invalid serial number')
                    pass
                pass
            else:
                raise TypeError('serial number must be the string type')
            pass
        except KeyError:
            pass

        try:
            _sn = kwargs['mbc_sn']
            if isinstance(_sn, str):
                if len(_sn) <= 16:
                    self.__mbc_sn = _sn
                    pass
                else:
                    raise ValueError('invalid MBC serial number')
                    pass
                pass
            else:
                raise TypeError('MBC serial number must be the string type')
            pass
        except KeyError:
            pass

        try:
            _sku = kwargs['sku']
            try:
                _is_force = True if kwargs['force_sku'] else False
                pass
            except KeyError:
                _is_force = False
                pass
            if isinstance(_sku, str):
                self.__parse_sku(_sku, _is_force)
                pass
            else:
                raise TypeError('sku number must be the string type')
            pass
        except KeyError:
            pass
        pass

    def set_breaker(self, value: bool):
        self.__breaker = value
        pass

    def get_breaker(self):
        return self.__breaker
        pass

    def set_fuse(self, index: int, value: bool):
        try:
            self.__fuse[index] = value
            pass
        except IndexError:
            raise ValueError('out of index')
        pass

    def get_fuse(self, index):
        try:
            return self.__fuse[index]
        except IndexError:
            raise ValueError('out of index')
        pass

    def set_type(self, index: int, va: int, vb: int, vc: int, vd: int):
        if index < self.__battery_num:
            self.__bat_type[index][0] = va
            self.__bat_type[index][1] = vb
            self.__bat_type[index][2] = vc
            self.__bat_type[index][3] = vd
            pass
        else:
            raise ValueError('out of index')
        pass

    def get_type(self, index: int):
        if index < self.__battery_num:
            return tuple(self.__bat_type[index])
        else:
            raise ValueError('out of index')
        pass

    def set_temperature(self, index: int, va: int, vb: int, vc: int, vd: int):
        if index < self.__battery_num:
            self.__bat_temp[index][0] = va
            self.__bat_temp[index][1] = vb
            self.__bat_temp[index][2] = vc
            self.__bat_temp[index][3] = vd
            pass
        else:
            raise ValueError('out of index')
        pass

    def get_temperature(self, index: int):
        if index < self.__battery_num:
            return tuple(self.__bat_temp[index])
        else:
            raise ValueError('out of index')
        pass

    def set_currents(self, index: int, value: int):
        if index < self.__battery_num:
            self.__current[index] = value
            pass
        else:
            raise ValueError('out of index')
        pass

    def get_current(self, index: int):
        if index < self.__battery_num:
            return self.__current[index]
        else:
            raise ValueError('out of index')
        pass

    def get_string_led_status(self) -> list:
        return self.__string_led

    def __parse_fw(self, fw: str):
        _fw_buf = fw.split('.')
        _data = (
            ('major', 0, 0xff),
            ('minor', 0, 0xff),
            ('deviation', 0, 0xff),
            ('build', 0, 0xffff)
        )
        for _i, _d in enumerate(_data):
            try:
                _v_s = _fw_buf[_i]
                try:
                    _v = int(_v_s)
                    if (_v >= _d[1]) and (_v <= _d[2]):
                        self.__fw[_d[0]] = _v
                        pass
                    else:
                        raise ValueError('{} range is {} ~ {}'.format(_d[0], 0, 0xff))
                    pass
                except ValueError:
                    raise ValueError('invalid firmware version {}'.format(fw))
            except IndexError:
                raise ValueError('invalid firmware version {}'.format(fw))
            pass
        pass

    def __parse_hw(self, hw: str):
        _hw_buf = hw.split('.')
        _data = (
            ('build', 0, 0xffffff),
            ('version', 0, 0xff),
            ('config', 0, 0xffffffff),
        )
        for _i, _d in enumerate(_data):
            try:
                _v_s = _hw_buf[_i]
                try:
                    _v = int(_v_s)
                    if (_v >= _d[1]) and (_v <= _d[2]):
                        self.__hw[_d[0]] = _v
                        pass
                    else:
                        raise ValueError('{} range is {} ~ {}'.format(_d[0], 0, 0xff))
                    pass
                except ValueError:
                    raise ValueError('invalid hardware version {}'.format(hw))
            except IndexError:
                raise ValueError('invalid hardware version {}'.format(hw))
            pass
        pass

    def __parse_sku(self, sku: str, force=False):
        # GVSMODBC6 (6 battery strings)
        # GVSMODBC6B (6 battery strings, cabinet with fuse)
        # GVSMODBC9 (9 battery strings)
        # GVSMODBC9B (9 battery strings, cabinet with fuse)

        _is_valid_sku = False
        try:
            # For invalid SKU test case
            self.__sku = sku[:16]
            self.__battery_num = 9

            _num_str = sku[8]
            try:
                _num = int(_num_str)
                if (_num == 6) or (_num == 9):
                    self.__sku = sku[:16]
                    self.__battery_num = _num
                    _is_valid_sku = True
                    pass
                else:
                    pass
                pass
            except ValueError:
                pass
            pass
        except IndexError:
            pass
        if _is_valid_sku is False:
            if force:
                self.__sku = sku[:16]
                # self.__battery_num = 9  # No need to set
                return
            print('WARNING:', '{} is invalid SKU'.format(sku))
            pass
        pass

    def _run(self):
        print('BMC {} is start'.format(self.__index))
        while True:
            try:
                _msg = self.__msg_queue.get(timeout=1)
                if _msg is None:
                    print('BMC {} is stop'.format(self.__index))
                    break
                    pass
                elif isinstance(_msg, can.Message):
                    self.__can_dev.send_message(_msg)
                    pass
                else:
                    pass
            except queue.Empty:
                self.send_message(0, bytearray((0, 0, 0, 0, 0, 0, 0, 0)))
                pass
            pass
        pass

    def on_message(self, msg_id: int, msg_data: bytearray):
        # print('[{}]{:0>4X}: {}'.format(self.__index, msg_id, ', '.join('{:0>2X}'.format(_v) for _v in msg_data)))
        if self.__run_state is True:
            try:
                _action, _is_need_data = self.__cmd_actions[msg_id]
                if _is_need_data:
                    _action(msg_data)
                    pass
                else:
                    _action()
                    pass
                pass
            except KeyError:
                pass
        pass

    def update_data(self):
        _val = 0
        for _i in range(10):
            for _j in range(4):
                self.__bat_type[_i][_j] = _val
                _val += 1
                if _val > 0xf:
                    _val = 0
            pass

        _val = -10
        for _i in range(10):
            for _j in range(4):
                self.__bat_temp[_i][_j] = _val
                _val += 2
                if _val > 80:
                    _val = 0
            pass
        for _i in range(10):
            self.__current[_i] = _i * 0x3f
            pass

        self.__fuse[0] = True
        self.__fuse[1] = True
        self.__breaker = True
        pass

    def __send_sn(self):
        _buf_l = bytearray(8)
        _buf_h = bytearray(8)
        _sn_b = bytearray(self.__sn, encoding='ascii')
        for _i, _v in enumerate(_sn_b):
            if _i < 8:
                _buf_l[_i] = _v
                pass
            else:
                _buf_h[_i - 8] = _v
                pass
            pass
        self.send_message(0x0004, _buf_l)
        self.send_message(0x0005, _buf_h)
        pass

    def __send_mbc_sn(self):
        _buf_l = bytearray(8)
        _buf_h = bytearray(8)
        _sn_b = bytearray(self.__mbc_sn, encoding='ascii')
        for _i, _v in enumerate(_sn_b):
            if _i < 8:
                _buf_l[_i] = _v
                pass
            else:
                _buf_h[_i - 8] = _v
                pass
            pass
        self.send_message(0x0013, _buf_l)
        self.send_message(0x0014, _buf_h)
        pass

    def __send_fw(self):
        _buf = bytearray(5)
        _buf[0] = self.__fw['major'] & 0xff
        _buf[1] = self.__fw['minor'] & 0xff
        _buf[2] = self.__fw['deviation'] & 0xff
        _buf[3] = (self.__fw['build'] >> 8) & 0xff
        _buf[4] = self.__fw['build'] & 0xff
        self.send_message(0x0001, _buf)
        pass

    def __send_hw(self):
        _buf = bytearray(8)
        _buf[0] = (self.__hw['build'] >> 16) & 0xff
        _buf[1] = (self.__hw['build'] >> 8) & 0xff
        _buf[2] = self.__hw['build'] & 0xff
        _buf[3] = self.__hw['version'] & 0xff
        for _i in range(4):
            _buf[4 + _i] = (self.__hw['config'] >> (3 - _i) * 8) & 0xff
            pass
        self.send_message(0x0006, _buf)
        pass

    def __send_sku(self):
        _buf_l = bytearray(8)
        _buf_h = bytearray(8)
        _sku_b = bytearray(self.__sku, encoding='ascii')
        for _i, _v in enumerate(_sku_b):
            if _i < 8:
                _buf_l[_i] = _v
                pass
            else:
                _buf_h[_i - 8] = _v
                pass
            pass
        self.send_message(0x0011, _buf_l)
        self.send_message(0x0012, _buf_h)
        pass

    def __send_fuse_and_breaker_state(self):
        _buf = bytearray(1)
        _buf[0] = 0x00
        if self.__fuse[1] is False:  # broken
            _buf[0] |= 0x04
            pass
        if self.__fuse[0] is False:  # broken
            _buf[0] |= 0x08
            pass
        if self.__breaker is False:  # off
            _buf[0] |= 0x10
            pass
        self.send_message(0x0124, _buf)
        pass

    def __send_current(self):
        _buf = bytearray(8)
        for _i in range(4):  # 0, 1, 2, 3
            _buf[_i * 2] = (self.__current[_i] >> 8) & 0xff
            _buf[_i * 2 + 1] = self.__current[_i] & 0xff
            pass
        self.send_message(0x0125, _buf)

        _buf = bytearray(4)
        for _i in range(4, 6):  # 4, 5
            _buf[(_i - 4) * 2] = (self.__current[_i] >> 8) & 0xff
            _buf[(_i - 4) * 2 + 1] = self.__current[_i] & 0xff
            pass
        self.send_message(0x0158, _buf)

        if self.__battery_num > 6:
            _buf = bytearray(8)
            for _i in range(6, 10):  # 6, 7, 8, 9
                _buf[(_i - 6) * 2] = (self.__current[_i] >> 8) & 0xff
                _buf[(_i - 6) * 2 + 1] = self.__current[_i] & 0xff
                pass
            self.send_message(0x0159, _buf)

        pass

    def __send_temperature(self):
        _id = (
            0x010C,
            0x010D,
            0x010E,
            0x010F,
            0x0128,
            0x0129,
            0x0154,
            0x0155,
            0x0156,
            0x0157
        )
        for _i in range(6):
            _buf = bytearray(4)
            _dat = self.__bat_temp[_i]
            _buf[0] = _dat[0] & 0xff
            _buf[1] = _dat[1] & 0xff
            _buf[2] = _dat[2] & 0xff
            _buf[3] = _dat[3] & 0xff
            self.send_message(_id[_i], _buf)
            pass
        if self.__battery_num > 6:
            for _i in range(6, 10):
                _buf = bytearray(4)
                _dat = self.__bat_temp[_i]
                _buf[0] = _dat[0] & 0xff
                _buf[1] = _dat[1] & 0xff
                _buf[2] = _dat[2] & 0xff
                _buf[3] = _dat[3] & 0xff
                self.send_message(_id[_i], _buf)
                pass
            pass
        pass

    def __send_battery_type(self):
        _id = [
            0x0108,
            0x0109,
            0x010A,
            0x010B,
            0x0126,
            0x0127,
            0x0150,
            0x0151,
            0x0152,
            0x0153
        ]
        for _i in range(6):
            _buf = bytearray(4)
            _dat = self.__bat_type[_i]
            _buf[0] = _dat[0] & 0xff
            _buf[1] = _dat[1] & 0xff
            _buf[2] = _dat[2] & 0xff
            _buf[3] = _dat[3] & 0xff
            self.send_message(_id[_i], _buf)
            pass

        if self.__battery_num > 6:
            for _i in range(6, 10):
                _buf = bytearray(4)
                _dat = self.__bat_type[_i]
                _buf[0] = _dat[0] & 0xff
                _buf[1] = _dat[1] & 0xff
                _buf[2] = _dat[2] & 0xff
                _buf[3] = _dat[3] & 0xff
                self.send_message(_id[_i], _buf)
                pass
            pass
        pass

    def __send_all_sample_data(self):
        self.__send_current()
        self.__send_battery_type()
        self.__send_temperature()
        self.__send_fuse_and_breaker_state()
        pass

    def __drive_led_1_6(self, msg_data: bytearray):
        for i in range(0, 6):
            stat = msg_data[i] if i < len(msg_data) else BmcNode.E_STRING_LED_OFF
            self.__string_led[i] = stat if i < len(self.__string_led) else self.__string_led.append(stat)

    def __drive_led_7_10(self, msg_data: bytearray):
        for i in range(6, 10):
            stat = msg_data[i - 6] if (i - 6) < len(msg_data) else BmcNode.E_STRING_LED_OFF
            self.__string_led[i] = stat if i < len(self.__string_led) else self.__string_led.append(stat)

    @staticmethod
    def __print_buf(_buf):
        print('buf:', ', '.join('{:0>2X}'.format(_v) for _v in _buf))
        pass

    pass


def main():
    # _can_dev = CanDevice(0)
    _can_dev = SimCanDevice('192.168.1.102', 8001)
    _can_dev.enable()
    _bmc_node = BmcNode(1, _can_dev)

    # 1
    print('Start first time')
    _bmc_node.config(
        hw='1.2.3',
        fw='4.5.6.7',
        sn='SN0123456789ABCD',
        sku='GVSMODBC6',
        mbc_sn='SN-EXTERNAL-MBC1')
    _bmc_node.start()
    time.sleep(10)
    _bmc_node.update_data()
    time.sleep(35)
    _bmc_node.stop()
    time.sleep(10)

    # 2
    print('Start second time')
    _bmc_node.config(hw='8.9.10',
                     # fw='11.12.13.14',
                     sn='SN-123456789abcd',
                     sku='GVSMODBC9',
                     mbc_sn='SN-EXTERNAL-MBCx')
    time.sleep(15)
    _bmc_node.start()
    time.sleep(35)
    _bmc_node.stop()
    _can_dev.disable()
    pass


if __name__ == '__main__':
    main()
    pass

