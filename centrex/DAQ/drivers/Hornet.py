import visa

class Hornet:
    def __init__(self, resource_name, address='01'):
        self.address = address # Factory default address=1
        self.rm = visa.ResourceManager()
        self.instr = self.rm.open_resource(resource_name)
        self.instr.baud_rate = 19200
        self.instr.data_bits = 8
        self.instr.parity = visa.constants.Parity.none
        self.instr.stop_bits = visa.constants.StopBits.one

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.instr.close()
        self.rm.close()

    def query(self, cmd):
        self.instr.write(cmd)
        # all responses are 13 characters long
        # (see manual, page 68)
        return self.instr.read_bytes(13).decode('ASCII')

    #################################################################
    ##########           SERIAL COMMANDS                   ##########
    #################################################################

    def ReadIonGaugePressure(self):
        """Read the current displayed pressure of the ion gauge in Torr.

        Returns:
        *xx_y.yyEzpp<CR> where y.yy = mantissa, z = sign of the exponent, i.e.,
        +/- and pp = the exponent.  (e.g., *01_1.53E-06<CR>)
        When IG is off: *01_9.90E+09
        """
        self.query("#" + self.address + "RD")

    def ReadSystemPressure(self):
        """Read the current IG pressure and CG pressure (IG+CG1 combined).

        Returns:
        *xx_y.yyEzyy<CR> (e.g., *01_1.53E-06<CR>)
        When IG is off: CG only
        """
        self.query("#" + self.address + "RDS")

    def ReadCGnPressure(self, n):
        """Read the current pressure for CGn.

        Returns:
        *xx_ y.yyEzyy <CR> (e.g., *01_7.60E+02<CR>)
        When CG is over-ranged or not plugged in: *01_1.01E+03<CR>
        """
        self.query("#" + self.address + "RDCG" + str(n))

    def SetAddrOffset(self, uu):
        """Set the communications (RS485) address offset (upper nibble).

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SA" + str(uu))

    def TurnIGOn(self):
        """Power up the filament and start reading pressure.

        Returns:
        *xx_PROGM_OK<CR>
        When CG controlled: ?01_INVALID_<CR>
        When IG error exists: ?01_INVALID_<CR>
        """
        self.query("#" + self.address + "IG1")

    def TurnIGOff(self):
        """Turns power OFF to the filament.

        Returns:
        *xx_PROGM_OK<CR> (clears any errors)
        """
        self.query("#" + self.address + "IG0")

    def ReadIGStatus(self):
        """Find out if filament is powered up and gauge is reading.

        Returns:
        *xx_0_IG_OFF<CR>
        *xx_1_IG_ON_<CR>
        """
        self.query("#" + self.address + "IGS")

    def TurnDegasOn(self):
        """Start a degas cycle.

        Returns:
        *xx_PROGM_OK<CR>
        When IG off: ?01_INVALID_<CR>
        When P > 5e-5: ?01_INVALID_<CR>
        """
        self.query("#" + self.address + "DG1")

    def TurnDegasOff(self):
        """Stop a degas cycle.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "DG0")

    def ReadDegasStatus(self):
        """Find out if the module is currently degassing.

        Returns:
        *xx_0_DG_OFF<CR>
        *xx_1_DG_ON_<CR>
        """
        self.query("#" + self.address + "DGS")

    def ReadEmissionCurrentStatus(self):
        """Read emission current setting.

        Returns:
        *xx_0.1MA_EM<CR>
        *xx_4.0MA_EM<CR>
        """
        self.query("#" + self.address + "SES")

    def SetEmissionCurrent(self, y):
        """Choose emission current of 4 mA or 100 muA.

        for y=1=4 mA; y=0=100muA

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SE" + y)

    def SetFilament(self, y):
        """Choose Filament 1 or 2.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SF" + y)

    def SetTripPointRelayI(self, val):
        """Set the 'turns on below' (+) pressure point for RLY I and set the
        'turns off above' (-) pressure point for RLY I as indicated by the
        pressure display for the ion gauge (IG).

        (e.g., #01SL+4.00E-06<CR>)
        (e.g., #01SL-5.50E-06<CR>)
        For the 'z' preceding the 'y.yy' value, a '+' = 'turns ON below' and a
        '-' = 'turns OFF above' the setpoint value for RLY I.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SL" + val)

    def SetTripPointRelayA(self, val):
        """Set the 'turns on below' (+) pressure point for RLY A and set the
        'turns off above' (-) pressure point for RLY A.
        
        Hint: Set the 'turns off above' (-) setpoint pressure first.
        
        NOTE: RLY A/B may be assigned to either CG1 or CG2 pressure readings.

        (e.g., #01SLA+4.00E+02<CR>)
        (e.g., #01SLA-5.00E+02<CR>)
        Turn the relay OFF (-) above 500 Torr.

        Returns:
        *xx_PROGM_OK<CR>

        If the 'turns off above' (-) pressure setpoint is less than the value of
        the 'turns on below' (+) setpoint, a syntax error of ?01 SYNTX ER<CR>
        will result.
        """
        self.query("#" + self.address + "SLA" + val)

    def SetTripPointRelayB(self, val):
        """Set the 'turns on below' (+) pressure point for RLY B and set the
        'turns off above' (-) pressure point for RLY B.
        
        Hint: Set the 'turns off above' (-) setpoint pressure first.
        
        (e.g., #01SLB+4.00E+02<CR>)
        (e.g., #01SLB-5.00E+02<CR>)
        Turn the relay OFF (-) above 500 Torr.

        Returns:
        *xx_PROGM_OK<CR>

        If the 'turns off above' (-) pressure setpoint is less than the value of
        the 'turns on below' (+) setpoint, a syntax error of ?01 SYNTX ER<CR>
        will result.
        """
        self.query("#" + self.address + "SLB" + val)

    def ReadTripPointRelayI(self, z):
        """Read the 'turns on below' (+) pressure point for relay I and read the
        'turns off above' (-) pressure point for relay I.

        (e.g., #01RL+<CR>)
        (e.g., #01RL-<CR>)

        Returns:
        *xx_y.yyEzyy<CR>
        (e.g., *01+7.60E+02<CR>
        (e.g., *01-7.60E+02<CR>)
        """
        self.query("#" + self.address + "RL" + z)


    def ReadTripPointRelayA(self, z):
        """Read the 'turns on below' (+) pressure point for relay A and read the
        'turns off above' (-) pressure point for relay A.

        (e.g., #01RLA+<CR>)
        (e.g., #01RLA-<CR>)

        Returns:
        *xx_y.yyEzyy<CR>
        (e.g., *01+5.60E+02<CR>)
        (e.g., *01-7.60E+02<CR>)
        """
        self.query("#" + self.address + "RLA" + z)


    def ReadTripPointRelayB(self, z):
        """Read the 'turns on below' (+) pressure point for relay B and read the
        'turns off above' (-) pressure point for relay B.

        (e.g., #01RLB+<CR>)
        (e.g., #01RLB-<CR>)

        Returns:
        *xx_y.yyEzyy<CR>
        (e.g., *01+5.60E+02<CR>)
        (e.g., *01-7.60E+02<CR>)
        """
        self.query("#" + self.address + "RLB" + z)

    def ReadIGStatus(self):
        """Finds out the cause of the ion gauge (IG) shutdown.

        Returns:
        *xx_00_ST_OK<CR>
        *xx_01_OVPRS<CR>
        *xx_02_EMISS<CR>
        *xx_08_POWER<CR>
        *xx_20_ION_C<CR>
        """
        self.query("#" + self.address + "RS")

    def SetCGnZero(self, n, val):
        """Set the zero or vacuum calibration point for CGn where n=1=A (as
        used in the command syntax) for CG1, n=2=B for CG2.

        Do not confuse the assignment of RLY A and RLY B with the distinction of
        A=CG1 and B=CG2 used here, in the command syntax.

        (e.g., #01TZA 0<CR>) floating point notation, or (e.g., #01TZB
        1.00e-2<CR>) scientific notation; either may be used with the ASCII
        format. When using float values, be sure to place a numeral in the
        placeholder immediately to the left of the decimal point.  TZn where n=A
        or B for CG1=A and CG2=B.

        Returns:
        *xx_PROGM_OK<CR>
        When P (i.e., x.xxE-pp) > 100mT: ?01_INVALID_<CR>
        When requested P > 100mT: ?01_INVALID_<CR>
        When requested gauge number <1 or >2: ?01_SYNTX_ER <CR>.
        """
        self.query("#" + self.address + "TZ" + n + " " + val)

    def SetCGnSpan(self, n, val):
        """Set the span or atmosphere calibration point for CGn.

        Returns:
        *xx_PROGM_OK<CR>
        When P < 400Torr: ?01_INVALID_<CR>
        When requested P < 400Torr: ?01_INVALID_<CR>
        When requested P > 1000mT: ?01_INVALID_<CR>
        When requested gauge number <1 or >2: ?01_SYNTX_ER <CR>
        """
        self.query("#" + self.address + "TS" + n + " " + val)

    def ReadSWVersion(self):
        """Read the revision number of the installed software.

        Returns:
        *xx_mmmm-vv<CR>
        e.g., *01_1769-103<CR>
        """
        self.query("#" + self.address + "VER")

    def SetFactoryDefaults(self):
        """Force unit to return ALL settings back to the way the factory
        programmed them before shipment.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "FAC")

    def SetBaudRate(self, val):
        """Set the communications baud rate for RS485.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SB" + val)

    def SetParity(self, val):
        """Set the communications to NO parity, 8 bits; ODD parity, 7 bits; EVEN
        parity, 7 bits for the RS485 interface.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SP" + val)

    def UnlockCommProgramming(self):
        """If the UNL command is enabled by the TLU command, the UNL command
        must be executed in sequence prior to the SB, SPN, SPO, and SPE
        commands.

        Not sending the UNL will yield a response of ?xx_COMM_ERR<CR>. If UNL is
        not enabled, then a response would be ?xx_SYNTX_ER<CR>.

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "UNL")

    def ToggleUNLFunction(self):
        """The TLU command will toggle the state of the UNL function. When the
        response is UL_ON, then UNL is required to execute SB, SPN, SPO, and
        SPE. When response is UL_OFF, then UNL is not required and sending a UNL
        will generate a response of ?xx_SYNTX_ER<CR>.

        Returns:
        *xx_1_UL_ON_<CR>
        *xx_0_UL_OFF<CR>
        """
        self.query("#" + self.address + "TLU")

    def Reset(self):
        """Reset the device as if power was cycled (Required to complete some of
        the commands.)

        Returns:
        No response.
        """
        self.query("#" + self.address + "RST")

    #################################################################
    ##########           NEW COMMANDS                      ##########
    ########## Note: these do not work on all devices.     ##########
    #################################################################

    def ReadPressureUnit(self):
        """Read pressure unit.

        Returns:
        *xx_TORR____<CR>
        *xx_MBAR____<CR>
        *xx_PASCAL__<CR>
        """
        self.query("#" + self.address + "RU")

    def SetPressureUnit(self, val):
        """Set Pressure unit for display and RD response.

        T = Torr, M = mBar, P = Pascal

        Returns:
        *xx_PROGM_OK<CR>
        """
        self.query("#" + self.address + "SU" + val)

    def ReadIGIonCurrent(self):
        """Read the current IG ion current in amps.

        Returns:
        *xx_y.yyEzyy<CR>
        (eg: *01_1.53E-06<CR>)
        When sensor is off: indicate offset voltage.
        """
        self.query("#" + self.address + "RDIGC")

    def ReadIGEmissionCurrent(self):
        """Read the actual IG emission current being measured by the gauge in
        amps.

        Returns:
        *xx_y.yyEzyy<CR>
        (eg: *01_1.00E-04<CR>)
        When sensor is off: 0.00E-00
        """
        self.query("#" + self.address + "RDIGE")

    def ReadIGFilamentVoltage(self):
        """Read the current IG filament voltage in volts.

        Returns:
        *xx_y.yyEzyy<CR>
        (eg: *01_1.20E-00<CR>)
        When sensor is off: 0.00E-00
        """
        self.query("#" + self.address + "RDIGV")

    def ReadIGFilamentCurrent(self):
        """Read the current IG filament current in amps.

        Returns:
        *xx_y.yyEzyy<CR>
        (eg: *01_2.20E-00<CR>)
        When sensor is off: 0.00E-00
        """
        self.query("#" + self.address + "RDIGI")