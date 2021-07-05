[TOC]

# Overview

A python library to simulate some features of BMC. This library works on both Linux and Windows.

# Installation
## Install `python-can` Library  
```bash
pip install python-can
```  
## Get Source Code
```bash
git clone https://github.schneider-electric.com/SESA432851/BMC-simulator.git
```
## For windows
```cmd
Windows 32-bit systems:
32-bit DLL(<repo>/win_lib/x86/PCANBasic.dll) > Windows\System32

Windows 64-bit systems:
32-bit DLL(<repo>/win_lib/x86/PCANBasic.dll) > Windows\SysWOW64
64-bit DLL(<repo>/win_lib/amd64/PCANBasic.dll) > Windows\System32
```
---
# API
## class CanDevice

This class provides the basic communication methods based on P-CAN(For windows) and SocketCan(For Linux)  
To create the instance for it, you need provide the device index.
- `__init__`  
    **device_index**: int type, it means which CAN device you will use, default is 0 if only one PCAN device is connected to your computer.

## class SimCanDevice
This class simulates the CAN communication by socket UDP protocol.  
It can only work in the ubuntu system.  
- `__init__`  
    **ip**: string type, the IP of SLC for CAN simulation  
    **port**: int type, the net port of SLC for CAN simulation  
    
- `enable`  
    Enable the device  

- `disable`  
    Disable the device  

## class BmcNode

One instance of BmcNode is to simulate one BMC board. You can create multiple BmcNode instances to simulate multiple BMC connected to SLC. It provides a list of APIs to control its behaviors.

- `__init__`  
    **index**: range 0 ~ 15, 0 -> id: 0x1A, 1 -> id: 0x11, 2 -> id: 0x12 ...  

    ```
    0x1A is the internal BMC  
    0x11 is the external BMC1  
    0x12 is the external BMC2   
    ...  
    ```
    **can_dev**: the can device instance

- `send_message`   
    Send a message by this device to SLC  
    **msg_id**: 16bit value, it is the id which is defined by BMC Can Protocol  
    **msg_data**: message data  

- `start`  
    Start this device as a BMC simulator. It simulate the power on of a BMC and will provide heartbeat signal to the SLC.

- `stop`  
    Stop this device as a BMC simulator. It will stop the heartbeat.

- `config`  
    Set static data for this device. These information should be set up before you start the simulator. If you need to change this, you should

    * Stop the simulator
    * Wait until SLC detect the heartbeat lost
    * Do the configuration
    * Start again

    **hw**: hardware version, its format as:  
    `'<HW ID>.<HW Rev>.<HW configuration>'` (for example: `'1.2.3'`)  

    |                  | size | Description                                                  |
    | ---------------- | ---- | ------------------------------------------------------------ |
    | HW ID            | 3    | The ID number in HEX is equivalent to the 0P number in Oracle, for the board. |
    | HW Rev           | 1    | The revision of the pcb. If revision number not available it must default to 0x00 |
    | HW configuration | 4    | Configuration represents partly the configuration of the device. The contents of these four bytes is dependant on the part number and can by that freely be defined for each part number. If configurationis not used it must default to 0x0000 |

    **fw**: firmware version, its format as:  
    `'<FW Major>.<FW Minor>.<Deviation>.<Build>'` (for example: `'4.5.6.7'`)    

    |           | size | Description                                                  |
    | --------- | ---- | ------------------------------------------------------------ |
    | FW Major  | 1    | Used to indicate a unique product ID or a major custom release ID  (Some product may have several major customer releases, for example Alpha product could have CR1 for the single unit, and CR2 for the parallel support) The major number is restricted to max 99. |
    | FW Minor  | 1    | Used to indicate that some new minor feature or bugfix change has been made. The Minor number must be changed for every officially release. |
    | Deviation | 1    | Used to indicate if version is a deviation or branch of the firmware. |
    | Build     | 2    | The build number is used to distinguish between iterations of code, and is used by R&D only. It is not intended as part of the released version number showed to the customer. |

    **sn**: serial number of BMC, TBD ('SN0123456789ABCD'), Max size: 16 bytes   
    **sku**: SKU number of MBC, its format as 'GVSMODBC6', Max size: 16 bytes  
    **mbc_sn**: serial number of MBC, TBD ('SN0123456789ABCD'), Max size: 16 bytes  

    ```
    GVSMODBC6 (6 battery strings)  
    GVSMODBC6B (6 battery strings, cabinet with fuse)  
    GVSMODBC9 (9 battery strings)  
    GVSMODBC9B (9 battery strings, cabinet with fuse)  
    ```  
    * Note  
    All properties can be got by the format `<BmcNodeInstance>.<property>`

- `set_breaker`  
    Set the breaker status  
    **value**: bool type 

    ```
    E_BREAKER_OFF = False
    E_BREAKER_ON = True
    ```  
- `get_breaker`  
    **return**: bool type, the breaker status

- `set_fuse`  
  Set the fuse status  
  **index**: int type, the fuse index, the range is 0 ~ 1  
  **value**: bool type
    E_BREAKER_OFF = False
    E_BREAKER_ON = True

- `get_fuse`   
  **index**: int type, the fuse index, the range is 0 ~ 1  
  **return**: bool type, the fuse status  

- `set_type`  
    **index**: int type, battery index, the range is 0 ~ 6/9  
    **va, vb, vc and vd**: int type, the battery type of group A B C and D  

    ```
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
    ```  
- `get_type`  
    **index**: int type, battery index, the range is 0 ~ 6/9  
    **return**: tuple type, (va, vb, vc, vd)

- `set_temperature`  
    **index**: int type, battery index, the range is 0 ~ 6/9  
    **va, vb, vc and vd**: int type, the temperature of group A B C and D, the range is -10 ~ 80  
    
- `get_temperature`  
    **index**: int type, battery index, the range is 0 ~ 6/9  
    **return**: tuple type, (va, vb, vc, vd)
    
# Demo  
## For P-CAN and SocketCAN
```python
import BmcNode
import time


def main():
    _can_dev = BmcNode.CanDevice(0)
    _bmc_node = BmcNode.BmcNode(1, _can_dev)
    _internal_bmc_node = BmcNode.BmcNode(0, _can_dev)

    # 1
    print('Start first time')
    _bmc_node.config(hw='1.2.3', fw='4.5.6.7', sn='SN-EXTERNAL-0001', sku='GVSMODBC6')
    _internal_bmc_node.config(hw='5.2.3', fw='4.7.6.7', sn='SN-INTERNAL-0000', sku='GVSMODBC9')
    _bmc_node.start()
    _internal_bmc_node.start()
    time.sleep(10)
    _bmc_node.set_breaker(BmcNode.BmcNode.E_BREAKER_ON)
    _bmc_node.set_temperature(3, 10, 20, 30, 40)
    time.sleep(15)
    _bmc_node.stop()
    time.sleep(10)

    # 2
    print('Start second time')
    _bmc_node.config(
        hw='8.9.10',
        fw='11.12.13.14',
        sn='SN-EXTERNAL-0123',
        sku='GVSMODBC9',
        mbc_sn='SN-EXTERNAL-MBC1')
    time.sleep(15)
    _bmc_node.start()
    time.sleep(10)
    _bmc_node.set_type(2,
                       BmcNode.BmcNode.E_BAT_TYPE_CP1270,
                       BmcNode.BmcNode.E_BAT_TYPE_HR1234WF2,
                       BmcNode.BmcNode.E_BAT_TYPE_LCR127R2P1,
                       BmcNode.BmcNode.E_BAT_TYPE_PXL12090)
    time.sleep(10)
    _bmc_node.set_fuse(0, BmcNode.BmcNode.E_FUSE_NORMAL)
    time.sleep(15)
    _bmc_node.stop()
    _internal_bmc_node.stop()
    pass


if __name__ == '__main__':
    main()
    pass
```
## For Socket Sim-CAN (Ubuntu)
```python
import BmcNode
import time


def main():
    _can_dev = BmcNode.SimCanDevice('127.0.0.1', 8001)
    _can_dev.enable()   # It is important
    _bmc_node = BmcNode.BmcNode(1, _can_dev)
    _bmc_node.config(hw='1.2.3', fw='4.5.6.7', sn='SN-EXTERNAL-SIM1', sku='GVSMODBC6')
    _bmc_node.start()
    time.sleep(20)
    _bmc_node.set_breaker(BmcNode.BmcNode.E_BREAKER_ON)
    _bmc_node.set_temperature(3, 10, 20, 30, 40)
    time.sleep(25)
    _bmc_node.stop()
    _can_dev.disable()  # To exit this precess, it is important
    pass


if __name__ == '__main__':
    main()
    pass
```
