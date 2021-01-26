import serial
import os
import time

from . import (
    DEBUG,
    DEVICE_IDS,
    BASE_PATH,
    BUFFER_SIZE,
    __version__
)


class Serial(serial.Serial):

    def read_decoded(self):
        tmp_data = self.read()

        while b'>>> ' not in tmp_data:
            tmp_data += self.read()

        return tmp_data.decode('utf-8')

    def communicate(self, data):
        DEBUG(data)
        data = bytes(data, encoding='utf-8')
        d_size = len(data)

        for num_bytes in range(0, d_size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, d_size - num_bytes)
            chunk = data[num_bytes: num_bytes + chunk_size]
            DEBUG(chunk)
            self.write(chunk)
            time.sleep(0.01)

        res = self.read_decoded()
        DEBUG(res)
        return res

    def init(self):
        # instead of sending the code to execute a command over and over again
        # like ampy is set up to do. I elected to house all of the functions
        # that are needed in a single file.
        #
        # The program checks for this files existance on the ESP32 and if the file
        # does exist it then checks the version of the file to make sure it is correct.
        # if the version is not correct I delete the file on the ESP32
        # If there is no file found either because it was deleted or the ESP32 did not
        # have it, I upload the file.
        #
        # Going this route actually adds a HUGE speed boost, the ESP32 has a small serial
        # buffer and limited processing power so it is easy to overrun the buffer.
        # So the maximum size transmit to and from the ESP32 is 32 bytes. So by sending
        # code that gets reused over and over again only a single time saves a large
        # amount of overhead.
        #
        # I also noticed that the ESP32 would quite often crash and reboot when using ampy.
        # I have a suspicision that it is due to fragmented memory when sending a large
        # amount of data. Since the ESP32 supports threading I decided to create a thread loop
        # that only has the single task of running a garbage collection every 1/2 a second.
        # I have not had the ESP32 crash at all so it must be working.

        esp32_control_file = os.path.join(BASE_PATH, 'esp32_control_file.py')

        with open(esp32_control_file, 'rb') as fle:
            esp32_control_file = fle.read()

        boot_data = self.read_decoded()
        DEBUG(self.boot_data)

        DEBUG(self.communicate('import os\r\n'))
        has_file = self.communicate('"esp32_control_file.py" in os.listdir("")\r\n')

        DEBUG(has_file)

        if 'True' in has_file:
            version = self.communicate("import esp32_control_file\r\n")
            DEBUG(version)
            if __version__ not in version:
                DEBUG(self.communicate('os.remove("esp32_control_file.py")\r\n'))

        has_file = self.communicate('"esp32_control_file.py" in os.listdir("")\r\n')
        DEBUG(has_file)

        if 'False' in has_file:
            DEBUG(self.communicate('f = open("esp32_control_file.py", "wb")\r\n'))

            cf_size = len(esp32_control_file)
            for cf_num_bytes in range(0, cf_size, BUFFER_SIZE - 14):
                cf_chunk_size = min(BUFFER_SIZE - 14, cf_size - cf_num_bytes)
                cf_chunk = repr(esp32_control_file[cf_num_bytes: cf_num_bytes + cf_chunk_size])

                if not cf_chunk.startswith("b"):
                    cf_chunk = "b" + cf_chunk

                DEBUG(self.communicate("f.write({0})\r\n".format(cf_chunk)))

            DEBUG(self.communicate('f.close()\r\n'))

        DEBUG(self.communicate("from esp32_control_file import *\r\n"))
        DEBUG(self.communicate("run_esp_32_control()\r\n"))

        return boot_data

    @staticmethod
    def get_port():
        try:
            # noinspection PyPackageRequirements
            import serial.tools.list_ports
        except ImportError:
            return None

        for prt in serial.tools.list_ports.comports():
            if prt.vid is None:
                continue

            for vid, pid in DEVICE_IDS:
                if vid == prt.vid and pid == prt.pid:
                    return prt.device
        return None
