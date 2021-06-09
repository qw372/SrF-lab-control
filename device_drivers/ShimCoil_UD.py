import numpy as np
import time
import logging
import traceback
import nidaqmx
import h5py


class ShimCoil_UD:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.update_aochannelUD(self.constr_param[0])
        self.update_trigchannel(self.constr_param[1])
        self.currentlimitUD = float(self.constr_param[4])
        self.update_turnon(self.constr_param[5])
        self.coilnameUD = self.constr_param[6]
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.samp_rate = 5000 # Samples/s

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (3,)

        # each element in self.warnings should be in format: [time.strftime("%H:%M:%S"), "warning content"]
        self.warnings = []

        try:
            self.currentUD = float(self.constr_param[2])
            self.timespan = float(self.constr_param[3])
        except Exception as err:
            self.init_error = ["error", "current/timespan setting error"]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        self.update_currentUD(self.currentUD)
        self.update_timespan(self.timespan)

        try:
            self.daq_ao_init()
            self.ao_task.close()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.ao_task.close()
        except Exception as err:
            pass

    def daq_ao_init(self):
        self.ao_task = nidaqmx.Task("ShimCoil_UD")
        self.ao_task.ao_channels.add_ao_voltage_chan(
                self.ao_channelUD,
                min_val=0,
                max_val=5,
                units=nidaqmx.constants.VoltageUnits.VOLTS
            )
        self.ao_task.timing.cfg_samp_clk_timing(
                rate = self.samp_rate,
                # source = "/Dev1/ai/SampleClock", # same source from this channel
                active_edge = nidaqmx.constants.Edge.RISING,
                sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan = self.samp_num
            )
        self.ao_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.trig_channel,
                trigger_edge = nidaqmx.constants.Edge.RISING
            )

    def ReadValue(self):
        if self.turnon:
            try:
                self.daq_ao_init()
                num_write = self.ao_task.write(self.output, auto_start=True, timeout=5.0)
                return_list = [self.currentUD, self.voltageUD]

                t = time.time()
                while not self.ao_task.is_task_done():
                    time.sleep(0.01)
                    if (time.time()-t) > 5.0:
                        # what if the DAQ is just triggered at the end of this period and doesn't have enough time to finish?
                        # anyway it should work the same as wait_until_done function, except it doesn't raise errors
                        return_list = [0, 0]
                        break

                self.ao_task.close()
                return [time.time()-self.time_offset, *return_list]

            except Exception as err:
                self.warnings.append([time.strftime("%H:%M:%S"), f"DAQ writing error.\n"+str(err)])
                self.ao_task.close()
                return [time.time()-self.time_offset, np.NaN, np.NaN]
        else:
            return [time.time()-self.time_offset, self.currentUD, 0]

    def update_aochannelUD(self, arg):
        self.ao_channelUD = arg

    def update_trigchannel(self, arg):
        self.trig_channel = arg

    def update_currentUD(self, arg):
        try:
            c = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert currentUD, current setting: {self.currentUD} A"])
            return

        if c > self.currentlimitUD:
            c = self.currentlimitUD
            self.warnings.append([time.strftime("%H:%M:%S"), f"currentUD settingn larger than limit, current setting: {c} A"])

        self.currentUD = c
        filename = 'C:/Users/dur!p5/github/SrF-lab-control/device_accessories/ShimCoil/LookUpTable_lastest.hdf'
        with h5py.File(filename, 'r') as f:
            lut = np.array(f[self.coilnameUD])
            lut_voltage = [lut[i][0] for i in range(len(lut))]
            lut_current = [lut[i][1] for i in range(len(lut))]
            self.voltageUD = np.interp(self.currentUD, lut_current, lut_voltage, left=lut_voltage[0], right=lut_voltage[-1])

            try:
                self.update_waveform()
            except AttributeError:
                pass

    def update_timespan(self, arg):
        try:
            t = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert, current time span setting: {self.timespan} ms"])
            return

        self.timespan = t
        self.update_waveform()

    def update_waveform(self):
        self.output = np.append(self.voltageUD*np.ones(int(self.timespan*self.samp_rate/1000)), 0)
        self.samp_num = len(self.output)

    def update_turnon(self, arg):
        self.turnon = bool(arg)

    def return_currentUD(self):
        return "{:.2f}".format(self.currentUD)

    def scan(self, type, val):
        if type == "current(A)":
            self.update_currentUD(val)
        else:
            self.warnings.append([time.strftime("%H:%M:%S"), f"scan type {type} not recognized."])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# trigchannel = "/Dev4/PFI1"
# timespan = 540
#
# aochannel1 = "Dev4/ao1"
# current1 = 2
# currentlimit1 = 5
# coilname1 = "Coil1"
#
# aochannel2 = "Dev4/ao2"
# current2 = 2
# currentlimit2 = 5
# coilname2 = "Coil2"
#
# aochannelUD = "Dev4/ao0"
# currentUD = 4
# currentlimitUD = 5
# coilnameUD = "CoilUD"
#
# turnon = True
#
# constr_params = [aochannel1, aochannel2, aochannelUD, trigchannel, current1, current2, currentUD, timespan, currentlimit1, currentlimit2, currentlimitUD, turnon, coilname1, coilname2, coilnameUD]
# with ShimCoil(time.time(), *constr_params) as s:
#     print(s.ReadValue())
#     print(s.GetWarnings())
#
#     s.update_currentUD(0)
