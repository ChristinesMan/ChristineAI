import ctypes
import time
import threading
import bcd
import smbus

import log
import status

# Poll the Pico for battery voltage every 60s
# I don't see a point in shutting down from here, because Pico will shutdown when it needs to
class Battery(threading.Thread):
    name = 'Battery'

    def __init__ (self):
        threading.Thread.__init__(self)

        # init var
        self.PowerState = 0
        self.ChargingState = 0

        # Track and report when power states change
        self.PowerStatePrev = 1
        self.PowerStateText = ['Power state undefined', 'Cable powered', 'Battery powered']
        self.ChargingStateText = ['Not Charging', 'Charging']

        # I'm not sure why but sometimes I/O errors occur, several times daily, so I'd like to report and gracefully recover from them
        # The pico and gyro are very securely connected and hardly any difference in wire lengths
        self.IOErrors = 0

    def run(self):
        log.battery.debug('Thread started.')

        try:

            # This is for reading and writing stuff from Pico
            bus = smbus.SMBus(1)

            while True:

                # fetch the readings from the Pico and handle I/O exceptions
                try:
                    status.BatteryVoltage = bcd.bcd_to_int(bus.read_word_data(0x69, 0x08))/1000
                    self.PowerState = bus.read_byte_data(0x69, 0x00)
                    self.ChargingState = bus.read_byte_data(0x69, 0x20)
                    self.IOErrors = 0

                except Exception as e:
                    # if 5 fails in a row, something is fucked, shut it down
                    self.IOErrors += 1
                    log.main.warning(f'I/O failure. ({self.IOErrors}) {e.__class__} {e} {log.format_tb(e.__traceback__)}')

                    if self.IOErrors >= 5:
                        log.main.critical('The battery thread has been shutdown.')
                        return

                # Log it
                log.battery.debug('%sV, %s, %s', status.BatteryVoltage, self.PowerStateText[self.PowerState], self.ChargingStateText[self.ChargingState])

                # if the power state changed, log it in the main log
                if self.PowerState != self.PowerStatePrev:
                    log.main.info('The power state changed from %s to %s', self.PowerStateText[self.PowerStatePrev], self.PowerStateText[self.PowerState])
                self.PowerStatePrev = self.PowerState

                # Copy to Global State
                status.PowerState = self.PowerStateText[self.PowerState]
                status.ChargingState = self.ChargingStateText[self.ChargingState]

                # I believe from reading Pico manual that the low battery beeping starts at 3.56V,
                # because 3.5V is the Pico low battery threshold for LiPO and it says it starts at 0.06V more than that.
                # But we switched to a lifepo4, so I need to figure out if these are correct or not. The voltage is much lower.
                # if self.BatteryVoltage <= 3.1:
                #     log.critical('Critical battery! Voltage: %s volts', self.BatteryVoltage)
                    # TellBreath(Request=Msg.Say, Data='conversation_no_02.wav')
                # elif self.BatteryVoltage <= 2.95:
                #     log.warning('Low battery! Voltage: %s', self.BatteryVoltage)
                    # TellBreath(Request=Msg.Say, Data='conversation_no_01.wav')

                time.sleep(60)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = Battery()
thread.daemon = True
thread.start()
