print('Loading Tilt Module...')

import asyncio
from uuid import UUID
from construct import Array, Byte, Const, Int8sl, Int16ub, Struct
from construct.core import ConstError
from bleak import BleakScanner

from modules.sensors.SensorBase import SensorBase
from modules.app_config import socketio, cache
from modules.sys_log import sys_log

class Tilt(SensorBase):
    
    def __init__(self, addr, uuid):
        self.addr = addr
        self.uuid = uuid
        self.t_cache = {'temp': 0, 'sg': 0, 'txpower': 0, 'rssi': 0}
        self.dev_name = SensorBase.sensor_type('SG')
        self.s_num = SensorBase.s_count['Total'] - 1
        cache['INIT'].append({'function': self.run_tilt, 'sleep': 5})
        cache['SENSORS'][self.s_num] = {'dev_id': self.uuid, 'com_type': 'ble', 'dev_name': self.dev_name, 'cur_read': "{0:.3f}".format(0)}

    def get_t_cache(self):
        return self.t_cache

    async def run_tilt(self, sleep):
        print("Starting Tilt Thread as Sensor %s" % self.s_num)  
        while True: 
            try:
                t = await BleakScanner.find_device_by_address(self.addr, 10)
                ad_data = t.details['props']['ManufacturerData'][0x004C]
                ibeacon = ibeacon_format.parse(ad_data)
                rssi = t.details['props']['RSSI']
                self.t_cache = {'temp': ibeacon.major, 'sg': float(ibeacon.minor)/10000, 'txpower': ibeacon.power, 'rssi': rssi}
                cache['SENSORS'][self.s_num]['cur_read'] = self.t_cache['sg']
                sys_log('t_cache: ' + str(self.t_cache))
            except Exception as e:
                sys_log('Run_tilt error: ' + str(e) + str(self.t_cache))
            await socketio.sleep(sleep)


tilts = {
    'a495bb10-c5b1-4b44-b512-1370f02d74de': 'Red',
    'a495bb20-c5b1-4b44-b512-1370f02d74de': 'Green',
    'a495bb30-c5b1-4b44-b512-1370f02d74de': 'Black',
    'a495bb40-c5b1-4b44-b512-1370f02d74de': 'Purple',
    'a495bb50-c5b1-4b44-b512-1370f02d74de': 'Orange',
    'a495bb60-c5b1-4b44-b512-1370f02d74de': 'Blue',
    'a495bb70-c5b1-4b44-b512-1370f02d74de': 'Yellow',
    'a495bb80-c5b1-4b44-b512-1370f02d74de': 'Pink'
}

# def add_calibration_point(x, y, field):
#     if isinstance(field, str) and field:
#         x1, y1 = field.split("=")
#         x = np.append(x, float(x1))
#         y = np.append(y, float(y1))
#     return x, y

# def calibrate(tilt, equation):
#     return eval(equation)

ibeacon_format = Struct(
    "type_length" / Const(b"\x02\x15"),
    "uuid" / Array(16, Byte),
    "major" / Int16ub,
    "minor" / Int16ub,
    "power" / Int8sl,
)

async def tilt_init():
    try:
        scanner = BleakScanner(device_found) #DBUS_FAST ERROR IS HERE
        await scanner.start()
        await socketio.sleep(3)
        await scanner.stop()
    except Exception as e:
        print('tilt_init error: ' + str(e))
            
async def device_found(device, advertisement_data):
    try:
        ad_data = advertisement_data.manufacturer_data[0x004C]
        ibeacon = ibeacon_format.parse(ad_data)
        uuid = str(UUID(bytes=bytes(ibeacon.uuid)))
        for key in tilts: 
            if uuid == key:
                if await unique(uuid):
                    addr = device.address
                    dev = Tilt(addr, uuid) 
    except KeyError:
        pass
    except ConstError:
        pass
    except Exception as e:
        print('Other device_found Error: ' + str(e))

a_tilts = []
async def unique(uuid):
    if uuid not in a_tilts:
        a_tilts.append(uuid)
        return True
    else:
        return False


tloop = asyncio.get_event_loop()
tloop.run_until_complete(tilt_init())
# finally: 
#     tloop.close()