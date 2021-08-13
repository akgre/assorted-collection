import socket
import time
from decimal import Decimal

class SfuClass:
    '''A Class representing a SFU 
    Allows remote control of a SFU using SCPI commands'''
    def __init__(self, common, sfuInst='', timeout=30, Debug=1):
        '''The Constructor
        Records the network name of the selected SFU'''   
        self.std = common['STD'].upper()          # standard being tested
        sfus = {'0': 'Dummy',
                'lh': 'localhost'} 
        
        if str(sfuInst) == '':
            sfuInst = str(common['sfu'])
            Debug = (1, 0)['N' in common.get('debugCTS', '')]
        self.id = sfus.get(str(sfuInst), 'Unable to find sfu {}'.format(str(sfuInst)))        
        self.BUFSIZ = 1024
        self.HOST = self.id
        self.PORT = 5025
        self.ADDR = (self.HOST, self.PORT)
        self.timeout = timeout
        self.debug = Debug
        if self.debug:
            print self.id
        if int(sfuInst) > 10 and int(sfuInst) < 9000:
            self.type = "Dektec"
        else:
            self.type = "SFU"
        
        print self.getSystemError()
        if self.debug:
            print self.systInfo()
        
        if self.type == "SFU":
            options = self.systOptions().split(',')
            self.dvbt       = 'SFU-K1' in options
            self.dvbc       = 'SFU-K2' in options
            self.dvbs       = 'SFU-K3' in options
            self.dvbs2      = 'SFU-K8' in options
            self.tdmbdab    = 'SFU-K11' in options
            self.tsplayer   = 'SFU-K20' in options
            self.arb        = 'SFU-K35' in options
            self.awgn       = 'SFU-K40' in options
            self.phaseNoise = 'SFU-K41' in options
            self.impulsiveNoise = 'SFU-K42' in options
            self.fading     = 'SFU-B30' in options
        elif self.type == "Dektec":
            self.dvbt       = True
            self.dvbc       = True
            self.dvbs       = True
            self.dvbs2      = True
            self.tdmbdab    = True
            self.tsplayer   = True
            self.arb        = True
            self.awgn       = True
            self.phaseNoise = True
            self.impulsiveNoise = True
            self.fading     = True
            
        # common settings usable by all standards:        
        self.SFUSetting  = {'base':         self.base,
                            'standard':     self.setStandard,
                            'power':        self.setRfLevel,
                            'pwrLimit':     self.setRfLimit,
                            'rfState':      self.setRfState,
                            'modState':     self.setModulationState,
                            'freq':         self.setFrequency,
                            'freqOff':      self.setFreqOff,
                            'snr':          self.setSnr,
                            'noiseState':   self.setNoise,
                            'noiseType' :   self.setNoiseType,
                            'fadingState':  self.setFadingState,
                            'intSource':    self.setInterfSource,
                            'intType':      self.setInterfType,
                            'intFreq':      self.setInterfFreq,
                            'intSigFreq':   self.setInterfSigSour,
                            'intNoise':     self.setInterfNoiseAdd,
                            'intAtt':       self.setInterfAtt,
                            'intLev':       self.setInterfLevel,
                            'intRef':       self.setInterfRef,
                            'arbFile':      self.setArb,
                            'arbState':     self.setArbState,
                            'arbClock':     self.setArbClock,
                            'iBurst':       self.setPulseNoiseBurst,
                            'iNoise':       self.setPulseNoise,
                            'pNoise' :      self.setPhaseNoise,
                            'phaseFile':    self.setPhaseShape,
                            'sigSource':    self.setSignalSource,
                            'arbState':     self.setArbState,
                            'noiseBW':      self.setNoiseBandwidth,
                            'noiseBWcoup':  self.setNoiseBwCoup,
                            'spectrum':     self.setSpectrum,
                            'TSfile':       self.setTsGenFile,
                            'TSstate':      self.setTsGenState,
                            'BERmeasStat':  self.setBerMeasState,
                            'BERrestart':   self.setBerMeasRestart,
                            'BERgateMode':  self.setBerGateMode,
                            'DTNormalise':  self.setDTFadNormalise,
                            'Attenuator':   self.setAttenuator,
                            'preset':       self.setFadingPreset,
                            'profile':      self.setFadingProfile,
                            'frameBurst':   self.setPulseNoiseFrameBurst,
                            'fadCommon':    self.setFadingCommon,
                            'arbFile':      self.setArb,
                            'pulseMinMax':  self.setPulseNoiseMinMax,
                            'IQScaling':    self.setArbGain}
        
        if self.std == 'DVBS2X' or self.std == 'DVBS2':
            self.SFUSetting['const']    = self.setDvbs2Const      # constellation settings (modulation):  4 (QPSK) 8 (8PSK) 16 (16APSK) 32 (32APSK)
            self.SFUSetting['codeRate'] = self.setDvbs2Coderate   # 1_4  1_3  2_5  1_2  3_5  2_3  3_4  4_5  5_6  6_7  7_8  8_9  9_10
            self.SFUSetting['baudrate'] = self.setDvbs2SymbolRate # 1000000 to 45000000 baud
            self.SFUSetting['pilots']   = self.setDvbs2Pilots     # Pilots state to ON or OFF
            self.SFUSetting['rollOff']  = self.setDvbs2RollOff    # roll-off settings are: 15 (0.15)  20 (0.20)  25 (0.25)  35 (0.35)
            self.SFUSetting['FECframe'] = self.setDvbs2FecFrame   # FEC frame length condition NORMAL for 64800 bit, SHORT for 16200 bit
            self.SFUSetting['signal']   = self.setDvbs2Source     # Sets DVB-S2X input signal source: EXT, TSPL or TEST
        if self.std == 'DVBS':
            self.SFUSetting['codeRate'] = self.setDvbsCoderate    # 1_4  1_3  2_5  1_2  3_5  2_3  3_4  4_5 5_6  6_7  7_8 1 8_9  9_10
            self.SFUSetting['baudrate'] = self.setDvbsSymbolRate  # 1000000 to 45000000 baud
            self.SFUSetting['signal']   = self.setDvbsSource        # Sets DVB-S input signal source: EXT, TSPL or TEST
            self.SFUSetting['const']    = self.setDvbsConst      # constellation settings (modulation):  4 (QPSK) 8 (8PSK) 16 (16APSK) 32 (32APSK)
            self.SFUSetting['rollOff']  = self.setDvbsRollOff    # roll-off settings are: 15 (0.15)  20 (0.20)  25 (0.25)  35 (0.35)
        if self.std == 'DVBT2':
            self.SFUSetting['FECframe']       = self.setT2FECFrame
            self.SFUSetting['codeRate']       = self.setT2CodeRate
            self.SFUSetting['const']          = self.setT2Const                              
            self.SFUSetting['constRot']       = self.setT2ConstRot  
            self.SFUSetting['timeIntType']    = self.setT2TimeIntType
            self.SFUSetting['timeIntFrame']   = self.setT2TimeIntFrame
            self.SFUSetting['timeIntLen']     = self.setT2TimeIntLength
            self.SFUSetting['plpNumBlocks']   = self.setT2DateNumBlock
            self.SFUSetting['bandwidth']      = self.setT2Bandwidth
            self.SFUSetting['bandwidthVar']   = self.setT2BandwidthVar
            self.SFUSetting['FFT_bwExt']      = self.setT2FFTSize
            self.SFUSetting['guard']          = self.setT2Guard
            self.SFUSetting['PP']             = self.setT2PilotPat
            self.SFUSetting['framesPerSuper'] = self.setT2FramesPerSuper
            self.SFUSetting['dataPerFrame']   = self.setT2DataPerFrame
            self.SFUSetting['slicesPerFrame'] = self.setT2SlicesPerFrame
            self.SFUSetting['networkMode']    = self.setT2NetworkMode
            self.SFUSetting['TxSystem']       = self.setT2TxSystem
            self.SFUSetting['PAPR']           = self.setT2PAPR
            self.SFUSetting['L1T2Version']    = self.setT2L1T2Version
            self.SFUSetting['L1PostMod']      = self.setT2L1PostMod
            self.SFUSetting['L1Rep']          = self.setT2L1Repetition
            self.SFUSetting['L1PostExt']      = self.setT2L1PostExtension
            self.SFUSetting['NumAuxStr']      = self.setT2NumAuxStream
            self.SFUSetting['L1RfSig']        = self.getT2L1RfSignalling
            self.SFUSetting['CellId']         = self.setT2CellId
            self.SFUSetting['NetworkId']      = self.setT2NetworkId
            self.SFUSetting['SystemId']       = self.setT2SystemId
            self.SFUSetting['T2MIState']      = self.setT2MIInterface
            self.SFUSetting['T2MISource']     = self.setT2MISource
            self.SFUSetting['T2MIpidId']      = self.setT2MIpidId
            self.SFUSetting['T2MIsidId']      = self.setT2MIsidId
            self.SFUSetting['groupRef']       = self.setDektecT2Group
            self.SFUSetting['FEFpayload']     = self.setT2EFEPayload
            self.SFUSetting['BBMode']         = self.setT2BBMode
            self.SFUSetting['standard']       = self.setStandard
            self.SFUSetting['t_bandwidth']    = self.setDvbtBand
            self.SFUSetting['t_fft']          = self.setDvbtFft
            self.SFUSetting['t_guard']        = self.setDvbtGuard
            self.SFUSetting['t_const']        = self.setDvbtCons
            self.SFUSetting['t_codeRate']     = self.setDvbtCoderate
            self.SFUSetting['t_usedBW']       = self.setDvbtUsedBand
            self.SFUSetting['t2_bandwidth']   = self.setT2Bandwidth
        if self.std == 'DVBT':
            self.SFUSetting['bandwidth'] = self.setDvbtBand
            self.SFUSetting['fft']       = self.setDvbtFft
            self.SFUSetting['guard']     = self.setDvbtGuard
            self.SFUSetting['const']     = self.setDvbtCons
            self.SFUSetting['codeRate']  = self.setDvbtCoderate
            self.SFUSetting['usedBW']    = self.setDvbtUsedBand
            self.SFUSetting['hierarchy'] = self.setDvbtHierarchy
            self.SFUSetting['codeRateLp']= self.setDvbtLpCoderate
            self.SFUSetting['source']    = self.setDvbtSource
            self.SFUSetting['sourceLp']  = self.setDvbtLpSource
            
        
        self.getSFUValue = {'standard':     self.getStandard,
                            'power':        self.getRfLevel,
                            'pwrLimit':     self.getRfLimit,
                            'rfState':      self.getRfState,
                            'modState':     self.getModulationState,
                            'freq':         self.getFrequency,
                            'freqOff':      self.getFreqOff,
                            'snr':          self.getSnr, 
                            'noiseState':   self.getNoise,
                            'noiseType' :   self.getNoiseType, 
                            'fadingState':  self.getFadingState, 
                            'intSource':    self.getInterfSource,
                            'intType':      self.getInterfType, 
                            'intFreq':      self.getInterfFreq, 
                            'intSigFreq':   self.getInterfSigSour,
                            'intNoise':     self.getInterfNoiseAdd, 
                            'intAtt':       self.getInterfAtt,
                            'intLev':       self.getInterfLevel,
                            'intRef':       self.getInterfRef, 
                            'arbFile':      self.getArb,
                            'arbState':     self.getArbState,
                            'arbClock':     self.getArbClock,
                            'iBurst':       self.getPulseNoiseBurst,
                            'iNoise':       self.getPulseNoise,
                            'pNoise' :      self.getPhaseNoise,
                            'phaseFile':    self.getPhaseShape,
                            'sigSource':    self.getSignalSource,
                            'noiseBW':      self.getNoiseBandwidth,
                            'noiseBWcoup':  self.getNoiseBwCoup,
                            'spectrum':     self.getSpectrum,
                            'TSfile':       self.getTsGenFile,
                            'TSstate':      self.getTsGenState,
                            'BERmeasStat':  self.getBerMeasState,
                            'BERgateMode':  self.getBerGateMode,
                            'frameBurst':   self.getPulseNoiseFrameBurst,
                            'fadCommon':    self.getFadingReference,
                            'Attenuator':   self.getAttenuator,
                            'profile':      self.getNoCommand,
                            'preset':       self.getNoCommand,
                            'pulseMinMax':  self.getPulseNoiseMinMax,
                            'IQScaling':    self.getArbGain}
        
        if self.std == 'DVBS2X' or self.std == 'DVBS2':
            self.getSFUValue['signal']     = self.getDvbs2Source     # Sets DVB-S2X input signal source: EXT, TSPL or TEST
            self.getSFUValue['FECframe']   = self.getDvbs2FecFrame   # FEC frame length condition NORMAL for 64800 bit, SHORT for 16200 bit
        if self.std == 'DVBS':
            self.getSFUValue['signal']     = self.getDvbsSource     # Sets DVB-S2X input signal source: EXT, TSPL or TEST
            #self.getSFUValue['FECframe']   = self.getDvbsFecFrame   # FEC frame length condition NORMAL for 64800 bit, SHORT for 16200 bit
        if self.std == 'DVBT2':
            self.getSFUValue['FECframe']       = self.getT2FECFrame
            self.getSFUValue['codeRate']       = self.getT2CodeRate
            self.getSFUValue['const']          = self.getT2Const                              
            self.getSFUValue['constRot']       = self.getT2ConstRot  
            self.getSFUValue['timeIntType']    = self.getT2TimeIntType
            self.getSFUValue['timeIntFrame']   = self.getT2TimeIntFrame
            self.getSFUValue['timeIntLen']     = self.getT2TimeIntLength
            self.getSFUValue['plpNumBlocks']   = self.getT2DateNumBlock
            self.getSFUValue['bandwidth']      = self.getT2Bandwidth
            self.getSFUValue['bandwidthVar']   = self.getT2BandwidthVar
            self.getSFUValue['FFT_bwExt']      = self.getT2FFTSize
            self.getSFUValue['guard']          = self.getT2Guard
            self.getSFUValue['PP']             = self.getT2PilotPat
            self.getSFUValue['framesPerSuper'] = self.getT2FramesPerSuper
            self.getSFUValue['dataPerFrame']   = self.getT2DataPerFrame
            self.getSFUValue['slicesPerFrame'] = self.getT2SlicesPerFrame
            self.getSFUValue['networkMode']    = self.getT2NetworkMode
            self.getSFUValue['TxSystem']       = self.getT2TxSystem
            self.getSFUValue['PAPR']           = self.getT2PAPR
            self.getSFUValue['L1T2Version']    = self.getT2L1T2Version
            self.getSFUValue['L1PostMod']      = self.getT2L1PostMod
            self.getSFUValue['L1Rep']          = self.getT2L1Repetition
            self.getSFUValue['L1PostExt']      = self.getT2L1PostExtension
            self.getSFUValue['NumAuxStr']      = self.getT2NumAuxStream
            self.getSFUValue['L1RfSig']        = self.getT2L1RfSignalling
            self.getSFUValue['CellId']         = self.getT2CellId
            self.getSFUValue['NetworkId']      = self.getT2NetworkId
            self.getSFUValue['SystemId']       = self.getT2SystemId
            self.getSFUValue['T2MIState']      = self.getT2MIInterface
            self.getSFUValue['T2MISource']     = self.getT2MIsetT2MISource
            self.getSFUValue['T2MIpidId']      = self.getT2MIpidId
            self.getSFUValue['T2MIsidId']      = self.getT2MIsidId
            self.getSFUValue['groupRef']       = self.getDektecT2Group
            self.getSFUValue['FEFpayload']     = self.getT2EFEPayload
            self.getSFUValue['BBMode']         = self.getT2BBMode
            self.getSFUValue['standard']       = self.getStandard
            self.getSFUValue['t_bandwidth']    = self.getDvbtBand
            self.getSFUValue['t_fft']          = self.getDvbtFft
            self.getSFUValue['t_guard']        = self.getDvbtGuard
            self.getSFUValue['t_const']        = self.getDvbtCons
            self.getSFUValue['t_codeRate']     = self.getDvbtCoderate
            self.getSFUValue['t_usedBW']       = self.getDvbtUsedBand
            self.getSFUValue['t2_bandwidth']   = self.getT2Bandwidth
        if self.std == 'DVBT':
            self.getSFUValue['bandwidth'] =  self.getDvbtBand
            self.getSFUValue['fft']       =  self.getDvbtFft
            self.getSFUValue['guard']     =  self.getDvbtGuard
            self.getSFUValue['const']     =  self.getDvbtCons
            self.getSFUValue['codeRate']  =  self.getDvbtCoderate
            self.getSFUValue['usedBW']    =  self.getDvbtUsedBand
            self.getSFUValue['hierarchy'] =  self.getDvbtHierarchy
            self.getSFUValue['codeRateLp']=  self.getDvbtLpCoderate
            self.getSFUValue['source']    =  self.getDvbtSource
            self.getSFUValue['sourceLp']  =  self.getDvbtLpSource
    
    def getNoCommand(self):
        return 'N/A'
        
    def setupSFU(self, setting, value):
        if self.SFUSetting.get(setting, False):
            if type(value) == list:
                var1 = value[0]
                var2 = value[1]
                return self.SFUSetting[setting](var1, var2)
            else:
                return self.SFUSetting[setting](value)
        else:
            #return '****    Error: No Setting {} Available    ****'.format(setting)
            return 'No Setting {} Available'.format(setting)
    
    def getSFUSetting(self, setting):
        if self.getSFUValue.get(setting, False):
            return self.getSFUValue[setting]()
        else:
            #return '****    Error: No Setting Value {} Available    ****'.format(setting)
            return 'No Setting Value {} Available'.format(setting)
        
    def dummyMode(self, txt):
        return "Dummy SFU Mode: {}".format(txt)      
    
    def writeSFU(self, cmd):
        '''Sends the command string cmd to the SFU if sfu1 or sfu2 are passed
        else it ignores the command i.e. in dummy SFU mode'''
        if self.id == 'Dummy':  return self.dummyMode(cmd)        
        if self.debug:  print "Setting SFU {} with {}".format(self.id, cmd) 
        try:
            self.sfuSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
            self.sfuSock.connect(self.ADDR)                    # connect a socket       
            self.sfuSock.send(cmd + "\n")                        # Send the command with end charater
            time.sleep((0, 0.1)[self.type == "SFU"])
            self.sfuSock.close()                          # Close the socket
        except:
            return "****    Comms Error - Unable to communicate with SFU: {}    ****".format(self.id)
        time.sleep((0, 0.5)[self.debug])  
        return True           
            
    def readSFU(self, cmd):
        '''Sends the command string cmd to the SFU if sfu1 or sfu2 are passed
        and then reads the reply, else it ignores the command i.e. in dummy 
        SFU mode. The reply from the SFU is returned in the string mesg.'''
        if self.id == 'Dummy':  return self.dummyMode(cmd)
        if self.debug:  print "Setting SFU {} with {}".format(self.id, cmd) 
        mesg = ""
        try:
            self.sfuSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
            self.sfuSock.settimeout(self.timeout)
            self.sfuSock.connect(self.ADDR)                    # connect a socket       
            self.sfuSock.send(cmd + "\n")                        # Send the command 
            mesg = self.sfuSock.recv(self.BUFSIZ)              # Read the response
            self.sfuSock.close()                          # Close the socket
            mesg = mesg.strip()                           # Remove \n at end of mesg
        except socket.timeout:
            if self.type == "SFU":
                mesg = "*****    Timeout    ***** - {}".format(self.getSystemError())
            if self.type == "Dektec":
                mesg = 'Timeout Error'
        except:
            return "****    Comms Error - Unable to communicate with SFU: {}    ***".format(self.id)
        time.sleep((0, 0.5)[self.debug])
        return mesg
    
    def querySFU(self, cmd, check='False'):
        '''Sends the command string cmd to the SFU if sfu1 or sfu2 are passed
        and then reads the reply, else it ignores the command i.e. in dummy 
        SFU mode. The reply from the SFU is returned in the string mesg.'''
        if self.id == 'Dummy':  return self.dummyMode(cmd)        
        mesg = ""
        if self.type == "SFU":
            if self.debug:  print "Setting SFU {} with {}".format(self.id, cmd)  
            #for connectAttempt in range(3):  # make up to 3 attempts get a good response from the instrument
                #if connectAttempt > 0:  print mesg, "\n__________            Connection Attempt " + str(connectAttempt+1) + "            __________"
            try:
                self.sfuSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
                self.sfuSock.settimeout(self.timeout)
                self.sfuSock.connect(self.ADDR)                    # connect a socket
                if 'OPC?' in cmd:
                    starttime = time.time()
                    if self.debug:
                        print "__________            Waiting for SFU operation to complete            __________"
                self.sfuSock.send(cmd + "\n")                        # Send the command
                mesg = self.sfuSock.recv(self.BUFSIZ)              # Read the response
                self.sfuSock.close()                          # Close the socket 
                if 'OPC?' in cmd and "" != mesg:
                    if self.debug:
                        print "__________            Operation took {} seconds            __________".format(time.time() - starttime)
                    mesg = "____    Operation Complete    _____"
                    #break
                elif mesg != "":
                    pass    #break
                else:
                    mesg = "Error - Returned Blank Message"
            except socket.timeout:
                mesg = "*****    Timeout    ***** - {}".format(self.getSystemError())
            except:
                mesg = "*************************                Comms Error - Unable to communicate with SFU: {}                *************************".format(self.id)
                
        elif self.type == "Dektec":
            cmdList = cmd.split(';')
            #for connectAttempt in range(3):
            #if connectAttempt > 0:  print mesg, "\n__________            Connection Attempt " + str(connectAttempt+1) + "            __________"
            for dektekCMD in cmdList:
                #print dektekCMD 
                if '?' in dektekCMD:
                    if 'OPC?' in dektekCMD:
                        mesg = "____    Operation Complete    _____"
                    else:
                        mesg = str(self.readSFU(dektekCMD))
                        if "" == mesg:
                            return 'N/A for DekTec'
                        #return mesg
                else:
                    if "*WAI" not in dektekCMD:
                        mesg = str(self.writeSFU(dektekCMD))
                #if 'Error' not in mesg: break     
                           
        time.sleep((0, 0.5)[self.debug])
          
        mesg = mesg.strip()   # Remove \n at end of mesg
        if 'Error' in mesg:
            check = 'False'
        if check != 'False':
            if check == 'ON' and mesg == '1':
                mesg = 'ON'
            elif check == 'OFF' and mesg == '0':
                mesg = 'OFF'
            if check == '':
                mesg = "********    SFU check value is blank\n    Command       = {}\n    Returned      = {}\n    Error Message = {}    \n********".format(cmd, mesg, self.getSystemError())           
            elif type(check) == str and check in mesg:
                if self.debug:  print 'Command Success:\n    Check Type   = {}\n    Check Value  = {}\n    Result Value = {}'.format(type(check), check, mesg) 
            elif type(check) == int and check == int(mesg):
                if self.debug:  print 'Command Success:\n    Check Type   = {}\n    Check Value  = {}\n    Result Value = {}'.format(type(check), check, mesg) 
            elif type(check) == Decimal and check == Decimal(mesg):
                if self.debug:  print 'Command Success:\n    Check Type   = {}\n    Check Value  = {}\n    Result Value = {}'.format(type(check), check, mesg) 
            else:
                mesg = "********    SFU check\n    Command       = {}\n    Returned      = {}\n    Error Message = {}    \n********".format(cmd, mesg, self.getSystemError())
        return mesg

#### Instrument Commands ###########################################################################
    
    def goLocal(self):
        ''' Returns the SFU to Local mode'''
        return "SFU set to local: {}".format(self.writeSFU("&GTL"))
            
    def checkSFU(self):
        '''Gets the SFU ID information'''
        return "SFU ID: {}".format(self.querySFU("*IDN?", "Rohde&Schwarz,SFU"))
    
    def versionInfo(self):
        '''Gets the SFU version information'''
        return "SFU Version: {}".format(self.querySFU("SYST:VERS?"))
    
    def systOptions(self):
        '''Gets the SFU version information'''
        return self.querySFU('*OPT?')
    
    def systInfo(self):
        '''Gets the SFU version information'''
        return "SFU System Information: {}".format(self.querySFU('SYST:INF:STAT?'))
    
    def preset(self):
        '''Resets the SFU to its default settings, equivalent to pressing the PRESET button'''
        return "SFU set to PRESET condition: {}".format(self.querySFU("*RST;*OPC?"))
    
    def screen(self):
        '''small REM message instead of LOCAL screen'''
        return "SFU screen ON: {}".format(self.querySFU("SYST:DISP:UPD ON;*OPC?"))
    
    def getSystemError(self):
        '''interrogate system for errors'''
        res = self.querySFU("SYST:ERR:ALL?")
        if self.type == 'Dektec':
            res = "____    DekTek - Unable to check for errors"          
        elif "No error" in res or "Dummy" in res:
            res = "____    SFU check - No Error Found"
        else:
            res = "****    SFU check - Error = {}".format(res)
        return res
    
    def base(self, profile):
        '''Loads a base settings .savrl file. A long delay is included to allow the instrument to set-up
        before retuning to local command and returning from the function.'''
        if self.type == 'SFU':
            print "____Loading Base File - This may take up to 30 seconds"
        saveTimeout = self.timeout
        self.timeout = 600
        self.querySFU(":MMEM:LOAD:STAT 1, \"{}\";*RCL 1;*OPC?".format(profile))
        self.timeout = saveTimeout
        errorCheck = self.getSystemError()
        if 'SFU check - Error' in errorCheck:
            return errorCheck
        return "Base config loaded: {}".format(profile)
    
    def RCL(self):
        '''Recalls a base setting .savrl file'''
        self.querySFU("*RCL 1;*OPC?")
        errorCheck = self.getSystemError()
        if 'SFU check - Error' in errorCheck:
            return errorCheck
        return "Base config recalled: *RCL 1"
    
    def setModulationState(self, state):
        '''Set the modulation state. state    "ON" | "OFF"'''
        return self.querySFU(":MOD {};*WAI;:MOD:STAT?".format(state), state)

    def getModulationState(self):
        '''Returns the modulation state.'''
        return self.querySFU(":MOD:STAT?")
    
    def setSignalSource(self, source):
        '''Set the modulation signal source. source    "INTern" | "DTV" | "ATV" | "ARB" | "DIGital" | "ANALog" |"DIRect"'''
        res = self.querySFU(":DM:SOUR {};*WAI;:DM:SOUR?".format(source), str(source))
        if '-222' in res:
            return '****    Error: This instrument does not have the {} feature'.format(source)
        return res

    def getSignalSource(self):
        '''Returns the modulation signal source.'''
        return self.querySFU(":DM:SOUR?")
    
    def setStandard(self, standard):
        '''Set the modulation standard.        
        standard    "DVBC" | "DVBS" | "DVBT" | "VSB" | "J83B" | "ISDB" | "DMBT" |
                    "DMBH" | "DVS2" | "DIR" | "TDMB" | "DTMB" | "T2DV" | "ATSM" |
                    "MED" | "CMMB"'''
        res = self.querySFU(":DM:TRAN {};*WAI;:DM:FORM?".format(standard), str(standard))
        if '-222' in res:
            return '****    Error: This instrument does not have the {} feature'.format(standard)
        return res

    def getStandard(self):
        '''Returns the modulation standard.'''
        return self.querySFU(":DM:TRAN?")

    def setAtvStandard(self, standard):
        '''Set the ATVtransmission standard.        
        standard    "BGPR" | "BGNP" | "DKPR" | "D1PR" | "DCPR" | "IPR" | "I1PR" |
                    "MNPR" | "LPR" | "BGRE" | "DKRE" | "IRE" | "MNRE" | "LRE" |"'''  
        res = self.querySFU(":DM:ATV:STAN {};*WAI;:DM:ATV:STAN?".format(standard), str(standard))
        if '-222' in res:
            return '****    Error: This instrument does not have the {} feature'.format(standard)
        return res

    def getAtvStandard(self):
        '''Returns the ATV transmission standard.'''
        return self.querySFU(":DM:ATV:STAN?")        
        
    def setSpectrum(self, state):
        '''Set the modulation spectrum state. state    "NORMal" | "INVerted"'''
        return self.querySFU("DM:POL {};*WAI;:DM:POL?".format(state), str(state))

    def getSpectrum(self):
        '''Returns the modulation spectrum state.'''
        return self.querySFU(":DM:POL?")

#### Noise Commands ###############################################################################     
    
    def getNoise(self):
        if self.awgn is False: return 'AWGN Noise function not available'  
        '''Gets the state of noise generator.'''
        return self.querySFU(":NOISE:STAT?")
     
    def setNoise(self, state):
        '''Sets the state of noise generator. state    "OFF" | "ADD" | "ONLY"'''
        state = (state, 'OFF')[self.type == "Dektec" and state == 'ONLY']
        return self.querySFU(":NOISE:STAT {};*WAI;:NOISE:STAT?".format(state), str(state))
    
    def setNoiseTypeOld(self, ntype):
        '''Sets the type of noise generator.
        Selecting a new type of noise will automatically de-selects the 
        currently enabled noise type.
        ntype    "AWGN" | "IMPULSE" | "PHASE"'''
        cmd = {"AWGN": ":NOISe:AWGN ON;*WAI;:NOISe:IMP OFF;*WAI;:NOISe:PHAS OFF;*WAI;:NOISe:AWGN?",
               "IMPULSE": ":NOISe:AWGN OFF;*WAI;:NOISe:IMP ON;*WAI;:NOISe:PHAS OFF;*WAI;:NOISe:IMP?",
               "PHASE": ":NOISe:AWGN OFF;*WAI;:NOISe:IMP OFF;*WAI;:NOISe:PHAS ON;*WAI;:NOISe:PHAS?"}.get(ntype)
        return self.querySFU(cmd, 'ON')  

    def setNoiseType(self, ntype):
        if not self.awgn: return 'AWGN Noise function not available'  
        '''Sets the type of noise generator.
        Selecting a new type of noise will not automatically de-selects the 
        currently enabled noise type.        
        ntype    "AWGN" | "IMPULSE" | "PHASE"'''
        noisesToAdd = ntype.split("+")          
        cmd = ":NOISe:AWGN {};*WAI;:NOISe:AWGN?".format(('OFF', 'ON')["AWGN" in noisesToAdd])
        state = ('OFF', 'ON')["AWGN" in noisesToAdd]
        AWGN_res = self.querySFU(cmd, state)
        cmd = ":NOISe:IMP {};*WAI;:NOISe:IMP?".format(('OFF', 'ON')["IMPULSE" in noisesToAdd])
        state = ('OFF', 'ON')["IMPULSE" in noisesToAdd]
        IMPULSE_res = self.querySFU(cmd, state)             
        cmd = ":NOISe:PHAS {};*WAI;:NOISe:PHAS?".format(('OFF', 'ON')["PHASE" in noisesToAdd])
        state = ('OFF', 'ON')["PHASE" in noisesToAdd]
        PHASE_res = self.querySFU(cmd, state)           
        return 'AWGN = {}, IMPULSE = {}, PHASE = {}'.format(AWGN_res, IMPULSE_res, PHASE_res)

    def getNoiseType(self):
        if not self.awgn: return 'AWGN Noise function not available'  
        '''Sets the type of noise generator.
        Selecting a new type of noise will not automatically de-selects the 
        currently enabled noise type.        
        ntype    "AWGN" | "IMPULSE" | "PHASE"'''  
        AWGN_res = ('OFF', 'ON')[self.querySFU(":NOISe:AWGN?") == '1']            
        IMPULSE_res = ('OFF', 'ON')[self.querySFU(":NOISe:IMP?") == '1']             
        PHASE_res = ('OFF', 'ON')[self.querySFU(":NOISe:PHAS?") == '1']            
        return 'AWGN = {}, IMPULSE = {}, PHASE = {}'.format(AWGN_res, IMPULSE_res, PHASE_res)

    def setSnr(self, snr):
        if not self.awgn: return 'AWGN Noise function not available'  
        '''Sets the level of SNR/CN,
        snr    -35 to 60'''
        snr = str(snr)
        noiseState = self.getNoise()
        if self.type == 'Dektec':
            if Decimal(snr) < 0 or Decimal(snr) > 30:
                return "*************************                Sweep Points Set Error - Invalid Value for DekTec {}                *************************".format(snr)
        else:
            if Decimal(snr) < -35 or Decimal(snr) > 60:
                return "*************************                Sweep Points Set Error - Invalid Value for SFU {}                *************************".format(snr)
        if 'ONLY' in noiseState and self.type == 'SFU':
            self.setNoise('OFF')      
        res = self.querySFU(":NOIS:CN {};*WAI;:NOIS:CN?".format(snr), Decimal(snr))
        if 'ONLY' in noiseState and self.type == 'SFU':
            self.setNoise('ONLY')
        return res

    def getSnr(self):
        if not self.awgn: return 'AWGN Noise function not available'  
        '''Returns the level of SNR/CN'''
        return self.querySFU(":NOIS:CN?")        
    
    def setNoiseBwCoup(self, state):
        '''Sets the state of the noise bandwidth coupling.        state    "OFF" | "ON"'''
        return self.querySFU(":NOIS:COUP {};*WAI;:NOISe:COUP?".format(state), state)
            
    def getNoiseBwCoup(self):
        '''Returns the state of the noise bandwidth coupling.'''
        return self.querySFU(":NOISe:COUP?")         

    def setNoiseBandwidth(self, bw):
        '''Sets the noise bandwidth.    freq        1MHz to 80MHz'''
        bw = str(bw)
        if Decimal(bw) < 1000000 or Decimal(bw) > 8000000:
            return '****    Error: Noise Bandwidth out of range'
        if self.getNoiseBwCoup() == '1':
            return '****    Error: To set Noise Bandwidth coupling must be OFF'
        return self.querySFU(":NOISE:BAND {};*WAI;:NOISE:BAND?".format(bw), int(bw))

    def getNoiseBandwidth(self):
        '''Returns the noise bandwidth.'''
        return self.querySFU(":NOISE:BAND?")

#### Phase Noise Commands #########################################################################
    def setPhaseNoise(self, ci):
        if not self.phaseNoise: return 'Phase Noise function not available'  
        '''Sets the level of Phase noise at 100Hz. ci    -110 to -12.9'''
        ci = str(ci)
        if Decimal(ci) < -110 or Decimal(ci) > -12.9:
            return '****    Error: Phase Noise out of range'
        return self.querySFU(":NOISe:PHAS:LEVel {};*WAI;:NOISe:PHAS:LEVel?".format(ci), Decimal(ci))
    
    def getPhaseNoise(self):
        if not self.phaseNoise: return 'Phase Noise function not available'  
        '''Sets the level of Phase noise at 100Hz. ci    -110 to -12.9'''
        return self.querySFU(":NOISe:PHAS:LEVel?")
                   
    def setPhaseShape(self, shape):
        if not self.phaseNoise: return 'Phase Noise function not available'  
        '''Sets the Phase noise shape file.        All phase noise shape files are located in the D:/PHASENOISE/ folder        shape    file name'''
        fileName = "D:/PHASENOISE/{}".format(shape)
        return self.querySFU(":NOISe:PHAS:SHAPe:SELect \"{}\";*WAI;:NOISe:PHAS:SHAPe:SEL?".format(fileName), str(shape))
    
    def getPhaseShape(self):
        if not self.phaseNoise: return 'Phase Noise function not available'  
        '''Returns the Phase noise shape file'''        
        return self.querySFU(":NOISe:PHAS:SHAPe:SEL?")

#### Impulsive Noise Commands #####################################################################
    
    def setPulseNoise(self, ci):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Sets the level of PULSE_NOISE/CI.        ci    -30 to 60'''
        ci = str(ci)
        if Decimal(ci) < -30 or Decimal(ci) > 60:
            return '****    Error: Phase Noise Pulse out of range'
        return self.querySFU(":NOISe:IMP:CI {};*WAI;:NOISe:IMP:CI?".format(ci), Decimal(ci))

    def getPulseNoise(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the level of Pulse noise.'''
        return self.querySFU(":NOISe:IMP:CI?")

    def setPulseNoiseBurst(self, burst):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Sets the number of PULSE_NOISE burst setting.        Burst      1 to 40,000'''
        burst = str(burst)
        if Decimal(burst) < 1 or Decimal(burst) > 40000:
            return '****    Error: Pulse Noise Burst out of range'
        return self.querySFU(":NOISe:IMP:PULS {};*WAI;:NOISe:IMP:PULS?".format(burst), Decimal(burst))
    
    def getPulseNoiseBurst(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Gets the number of PULSE_NOISE burst setting.        Burst      1 to 40,000'''
        return self.querySFU(":NOISe:IMP:PULS?")

    def setPulseNoiseFrame(self, frame):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the frame duration setting.     Frame      10 | 100 | 1000 '''
        frame = str(frame)
        return self.querySFU(":NOISe:IMP:FRAMe {} ms;*WAI;:NOISe:IMP:FRAMe?".format(frame), Decimal(frame)/1000)
    
    def setPulseNoiseFrameBurst(self, frame, burst):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Sets the level of PULSE_NOISE frame and burst setting.        Frame      10 | 100 | 1000           Burst      1 to 40,000'''
        frameRes = self.setPulseNoiseFrame(frame)
        burstRes = self.setPulseNoiseBurst(burst)   
        return 'Frame = {}, Pulse = {}'.format(frameRes, burstRes)
    
    def getPulseNoiseFrameBurst(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Sets the level of PULSE_NOISE frame and burst setting.        Frame      10 | 100 | 1000          Burst      1 to 40,000'''
        res1 = self.querySFU(":NOISe:IMP:FRAMe?")
        res2 = self.querySFU(":NOISe:IMP:PULS?")    
        return 'Frame = {}, Pulse = {}'.format(res1, res2)
        
    def setPulseNoiseMinMax(self, minPulse, maxPulse):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Sets the  min and max setting.
        The min and max values are dependent on the frame and burst settings.
        Also min can never be set higher than max and max can never be set lower
        than min. Therefore to ensure these are set correctly, they need to be set to
        absoulet min and max setting first. 
        Min        250ns
        Max        10s / (pulses per burst - 1)'''
        minPulse = str(minPulse)
        maxPulse = str(maxPulse)      
        minCheck = Decimal(Decimal(minPulse)/1000000).quantize(Decimal('0.0000000'))
        maxCheck = Decimal(Decimal(maxPulse)/1000000).quantize(Decimal('0.0000000'))
          
        res1 = self.querySFU(":NOISe:IMP:MINS 0.00000025;:NOISe:IMP:MINS?", Decimal('0.0000002'))   # Set min space to minimum level
        if "Error" in res1:
            return res1                    # Check min space is set without error
        if Decimal(minPulse) < 0.25 or Decimal(minPulse) > 16384:
            return '****    Error: Pulse Noise Min out of range'
        if Decimal(maxPulse) < 0.25 or Decimal(maxPulse) > 16384:    # Check frame duration and pulses per burst as that will determine the max setting
            return '****    Error: Pulse Noise Max out of range'
        resMax = self.querySFU(":NOISe:IMP:MAXS {} us;:NOISe:IMP:MAXS?".format(maxPulse), maxCheck)                      # Read max space
        resMin = self.querySFU(":NOISe:IMP:MINS {} us;:NOISe:IMP:MINS?".format(minPulse), minCheck)                       # Read min space
        return  'Max = {}, Min = {}'.format(resMax, resMin)
    
    def getPulseNoiseMinMax(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        resMax = self.querySFU(":NOISe:IMP:MAXS?")                      # Read max space
        resMin = self.querySFU(":NOISe:IMP:MINS?")                       # Read min space
        return  'Max = {}, Min = {}'.format(resMax, resMin)
    
    def getPulseNoiseFrame(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the frame duration setting.'''
        return self.querySFU(":NOISe:IMP:FRAMe?")
    
    def getPulseNoisePulses(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the number of pulses per burst setting.'''
        return self.querySFU(":NOISe:IMP:PULS?")
    
    def getPulseNoiseMin(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the minumin pulse spaceing setting.'''
        return self.querySFU(":NOISe:IMP:MINS?")
    
    def getPulseNoiseMax(self):
        if not self.impulsiveNoise: return 'Impulsive Noise function not available'
        '''Returns the maxumin pulse spaceing setting.'''
        return self.querySFU(":NOISe:IMP:MAXS?")
        
#### Frequency and Level Commands #################################################################
    def setFrequency(self, freq):
        '''Sets the carrier frequency.        freq        300 kHz to 3GHz'''
        freq = str(freq)
        if Decimal(freq) < 300000 or Decimal(freq) > 3000000000:
            return '****    Error: Main Frequency out of range'
        return self.querySFU(":FREQ {};FREQ?".format(freq), Decimal(freq))
    
    def setFreqOff(self, offset):
        '''Sets a carrier frequency offset.
        Note: this is different to the SFU carrier frequency offset command which dosn't actutualy do anything.
        The value of current carrier frequency is read then the offset added to this value.
        The carrier frequency is then reset with the offset added.'''
        offset = str(offset)
        return self.setFrequency(Decimal(self.getFrequency()) + Decimal(offset))

    def getFrequency(self):
        '''Returns the carrier frequency.'''
        return self.querySFU(":FREQ?")
    
    def getFreqOff(self):
        '''Returns the carrier frequency offset.'''
        if self.type == "Dektec":
            return self.querySFU(":FREQ?")
        return self.querySFU(":FREQ:OFFS?")
    
    def setRfLevelAndState(self, level, state):
        '''Sets the RF level and its state.    level    -120 to 0        state    "OFF" | "ON"'''
        return 'Level = {}, State = {}'.format(self.setRfLevel(level), self.setRfState(state))
 
    def setRfLevel(self, level):
        '''Sets the RF level.        level    -120 to 0'''
        level = str(level)
        if Decimal(level) < -120 or Decimal(level) > 0:
            return '****    Error: RF Output Level out of range'
        return self.querySFU("UNIT:VOLT DBM;:POW {};*WAI;:POW?".format(level), Decimal(level))

    def setRfState(self, state):
        '''Sets the RF state.   state    "OFF" | "ON"'''
        return self.querySFU(":OUTP {};*WAI;:OUTP?".format(state), state)
    
    def setALC(self, state):
        '''Sets the ALC state.         state    "AUTO" | "ON"| "OFF" '''
        return self.querySFU(":POW:ALC:STAT {};*WAI;:POW:ALC:STAT?".format(state), state)
    
    def getALC(self):
        '''Gets ALC State        '''
        return self.querySFU(":POW:ALC:STAT?")
    
    def setAttenuator(self, state):
        '''Sets the RF state.         state    "AUTO" | "FIX"| "NORM"| "HPOW"'''
        self.querySFU(":OUTP:AMOD AUTO;*WAI;:OUTP:AMOD?".format(state), 'AUTO')
        rfPower = self.getRfLevel() 
        setAttenuator = self.querySFU(":OUTP:AMOD {};*WAI;:OUTP:AMOD?".format(state), state)
        rfPower = self.setRfLevel(rfPower) 
        return setAttenuator
    
    def getAttenuator(self):
        '''Sets the RF state.         state    "AUTO" | "FIXED"| "NORMAL"| "HPOWER"'''
        return self.querySFU(":OUTP:AMOD?")
    
    def getAttenuatorUpper(self):
        '''Gets the RF Upper Attenuator Limit.        '''
        return self.querySFU(":OUTP:AFIX:RANG:UPP?")
        
    def setRfLimit(self, limit):
        '''Sets the RF level.       level    -120 to 20'''
        limit = str(limit)
        if Decimal(limit) < -120 or Decimal(limit) > 20:
            return '****    Error: RF Output Level Limit out of range'
        return self.querySFU(":POW:LIM {};*WAI;:POW:LIM?".format(limit), Decimal(limit))
        
    def setRfLevelOffs(self, offset):
        '''Sets the RF level offset.        level    -120 to 120'''
        offset = str(offset)
        if Decimal(offset) < -120 or Decimal(offset) > 120:
            return '****    Error: RF Output Level Limit out of range'
        return self.querySFU(":POW:OFFS {};*WAI;:POW:OFFS?".format(offset), Decimal(offset))

    def getRfLevel(self):
        '''Returns the RF level.'''
        return self.querySFU(":POW?")
    
    def getRfState(self):
        '''Returns the state of the RF output.'''
        return self.querySFU(":OUTP?") 
        
    def getRfLimit(self):
        '''Returns the state of the RF output.'''
        return self.querySFU(":POW:LIM?") 
        
    def getRfLevelOffs(self):
        '''Returns the value of the RF output offset.'''
        return self.querySFU(":POW:OFFS?") 
        
    def setRfVoltage(self, level):
        '''Sets the RF voltage.        level    -120 to 20'''
        level = str(level)
        if Decimal(level) < -120 or Decimal(level) > 20:
            return '****    Error: RF Output Level Limit out of range'
        return self.querySFU(":VOLT {};*WAI;:VOLT?".format(level), str(level))
     
    def setRfUnit(self, unit):
        '''Sets the RF level unit.        unit    DBM for dBm, DBUV for dBuV, DBMV for dBmV and MV for mV'''
        return self.querySFU("UNIT:VOLT {};*WAI;:UNIT:VOLT?".format(unit), str.upper(unit))
        
    def getRfVoltage(self):
        '''Returns the RF level.'''
        return self.querySFU(":VOLT?") 
        
    def getRfUnit(self):
        '''Returns the value of the RF level unit.'''
        return self.querySFU("UNIT:VOLT?") 
    
#### Fading Sim comands ###########################################################################

    def setFadingState(self, state):
        if not self.fading: return 'Fading function not available'
        '''Sets the state of fading simulator.        state    "OFF" | "ON" '''
        return self.querySFU(":FSIM1:STAT {};*WAI;:FSIM:STAT?".format(state), state)
    
    def getFadingState(self):
        if not self.fading: return 'Fading function not available'
        '''Returns the state of fading simulator.'''
        return self.querySFU(":FSIM:STAT?")
    
    def setFadingProfile(self, profile):
        if not self.fading: return 'Fading function not available'
        '''Loads a fading profile .fad file'''
        #profileCheck = self.querySFU(":MMEM:CDIR \"" + profile + "\";:FSIM:CAT?")
        #if profileCheck is not profile:
        #    return "Error: Fading config " + profile + " not found"
        self.querySFU(":FSIM1:LOAD \"{}\";*OPC?".format(profile))
        errorCheck = self.getSystemError()
        if 'SFU check - Error' in errorCheck:
            return errorCheck
        return "Fading config loaded: {}".format(profile)
    
    def setFadingPreset(self, preset):
        if not self.fading: return 'Fading function not available'
        '''Loads a preset standard fading profile'''
        return self.querySFU(":FSIM1:STAN {};*WAI;*OPC?".format(preset))
    
    def getFadingPreset(self):
        if not self.fading: return 'Fading function not available'
        '''Returns the loaded preset standard fading profile'''
        return self.querySFU(":FSIM1:STAN?")
    
    def setFadingSet(self, groupNumber, pathNumber, parameter, value):
        if not self.fading: return 'Fading function not available'
        '''Sets 1 of 14 fading parameter in a specified group and path''' 
        parameter = int(parameter)
        value = str(value)
        if value in ['ON', 'OFF']: 
            value = value            
        cmd = {0:   ":FSIM1:DEL:GRO{0}:PATH{1}:LOSS {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:LOSS?".format(groupNumber, pathNumber, value),   #PATH LOSS   
               1:   ":FSIM1:DEL:GRO{0}:BDELay {1};*WAI;:FSIM1:DEL:GRO{0}:BDELay?".format(groupNumber, value),                           #Basic Delay
               2:   ":FSIM1:DEL:GRO{0}:PATH{1}:ADELay {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:ADELay?".format(groupNumber, pathNumber, value), #Addit Delay
               3:   ":FSIM1:DEL:GRO{0}:PATH{1}:PRATio {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:PRATio?".format(groupNumber, pathNumber, value), #Power Ration
               4:   ":FSIM1:DEL:GRO{0}:PATH{1}:CPHase {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:CPHase".format(groupNumber, pathNumber, value),#Const Phase
               5:   ":FSIM1:DEL:GRO{0}:PATH{1}:CPHase {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:CPHase".format(groupNumber, pathNumber, value),#Speed
               6:   ":FSIM1:DEL:GRO{0}:PATH{1}:FRATio {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:FRATio?".format(groupNumber, pathNumber, value), #Freq Ratio
               7:   ":FSIM1:DEL:GRO{0}:PATH{1}:CORR:COEFficient {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:CORR:COEFficient".format(groupNumber, pathNumber, value),#Coefficient
               8:   ":FSIM1:DEL:GRO{0}:PATH{1}:CORR:PHASe {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:CORR:PHASe?".format(groupNumber, pathNumber, value),#Phase
               9:   ":FSIM1:DEL:GRO{0}:PATH{1}:LOGN:LCONstant {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:LOGN:LCONstant?".format(groupNumber, pathNumber, value),#Phase
               10:  ":FSIM1:DEL:GRO{0}:PATH{1}:LOGN:CTSD {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:LOGN:CTSD?".format(groupNumber, pathNumber, value),#Standard Dev
               11:  ":FSIM1:DEL:GRO{0}:PATH{1}:FDOP {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:FDOP?".format(groupNumber, pathNumber, value),#Doppler frq
               12:  ":FSIM1:DEL:GRO{0}:PATH{1}:STAT {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:STAT?".format(groupNumber, pathNumber, value),#State
               13:  ":FSIM1:DEL:GRO{0}:PATH{1}:PROF {2};*WAI;:FSIM1:DEL:GRO{0}:PATH{1}:PROF?".format(groupNumber, pathNumber, value)}.get(parameter, False)#Profile
        if not cmd:
            return '****    Invalid settings for groupNumber = {}, pathNumber = {}, parameter = {}, value = {}'.format(groupNumber, pathNumber, parameter, value)
        return self.querySFU(cmd)#, Decimal(value))
 
    def getFadingSet(self, groupNumber, pathNumber, parameter):
        if not self.fading: return 'Fading function not available'
        '''Returns 1 of 14 fading parameter in a specified group and path '''
        parameter = int(parameter)
        
        cmd = {0:  ":FSIM1:DEL:GRO{0}:PATH{1}:LOSS?".format(groupNumber, pathNumber), #PATH LOSS  
               1:  ":FSIM1:DEL:GRO{0}:BDELay?".format(groupNumber), #Basic Delay
               2:  ":FSIM1:DEL:GRO{0}:PATH{1}:ADELay?".format(groupNumber, pathNumber), #Addit Delay
               3:  ":FSIM1:DEL:GRO{0}:PATH{1}:PRATio?".format(groupNumber, pathNumber),#Power Ration
               4:  ":FSIM1:DEL:GRO{0}:PATH{1}:CPHase".format(groupNumber, pathNumber),#Const Phase
               5:  ":FSIM1:DEL:GRO{0}:PATH{1}:SPEed?".format(groupNumber, pathNumber),#Speed
               6:  ":FSIM1:DEL:GRO{0}:PATH{1}:FRATio?".format(groupNumber, pathNumber),#Freq Ratio
               7:  ":FSIM1:DEL:GRO{0}:PATH{1}:CORR:COEFficient".format(groupNumber, pathNumber),#Coefficient
               8:  ":FSIM1:DEL:GRO{0}:PATH{1}:CORR:PHASe?".format(groupNumber, pathNumber),#Phase
               9:  ":FSIM1:DEL:GRO{0}:PATH{1}:LOGN:LCONstant?".format(groupNumber, pathNumber),#Local Constant
               10: ":FSIM1:DEL:GRO{0}:PATH{1}:LOGN:CTSD?".format(groupNumber, pathNumber),#Standard Dev
               11: ":FSIM1:DEL:GRO{0}:PATH{1}:FDOP?".format(groupNumber, pathNumber),#Doppler frq
               12: ":FSIM1:DEL:GRO{0}:PATH{1}:STAT?".format(groupNumber, pathNumber),#State
               13: ":FSIM1:DEL:GRO{0}:PATH{1}:PROF?".format(groupNumber, pathNumber)}.get(parameter, False)#Profile
        if not cmd:
            return '****    Invalid settings for groupNumber = {}, pathNumber = {}, parameter = {}, value = {}'.format(groupNumber, pathNumber, parameter)
        return self.querySFU(cmd)

    def setFadingReference(self, reference):
        if not self.fading: return 'Fading function not available'
        '''Sets the ref setting for the fading simulator [SPEED | DOPPLER]'''
        check = ("FDOP", "SPE")[reference == "SPEED"]
        return self.querySFU(":FSIM:REF {};*WAI;:FSIM:REF?".format(check), check)

    def getFadingReference(self):
        if not self.fading: return 'Fading function not available'
        '''Returns the ref setting for the fading simulator [SPEED - DOPPLER]'''
        return self.querySFU(":FSIM:REF?")

    def setFadingCommon(self, allPaths):
        if self.fading is False: return 'Fading function not available'
        '''Sets the common path setting for the fading simulator [ON | OFF]'''
        # find out if in speed or doppler mode
        res = self.querySFU(":FSIM:REF?")  
        if "FDOP" in res:
            res = self.querySFU(":FSIM:CFD {};*WAI;:FSIM:CFD?".format(allPaths), allPaths)
        elif "SPE" in res:
            res = self.querySFU(":FSIM:CSP {};*WAI;:FSIM:CSP?".format(allPaths), allPaths)      
        return res
    
    def getFadingCommon(self):
        if not self.fading: return 'Fading function not available'
        '''Returns the common path setting for the fading simulator'''
        # find out if in speed or doppler mode
        queRes = self.querySFU(":FSIM:REF?") 
        res = {"FDOP": self.querySFU(":FSIM:CFD?"),
               "SPE": self.querySFU(":FSIM:CSP?")}.get(queRes, queRes)
        return res    

    def setDTFadNormalise(self):
        if not self.fading: return 'Fading function not available'
        ''' Dektec only command. Normalise the level of the paths set in the Dektec fadding simulator'''
        return "Dektec Fading Normalise set: ".format(self.querySFU(":FSIM:NORM"))
    
#### TS Gen Commands ##############################################################################
            
    def setTsGenState(self, state):
        if not self.tsplayer: return 'TS player function not available'
        '''Sets the state of the transport stream player [STOP-PAUSE-PLAY]'''
        check = {"PAUSE": "PAUS", "PLAY": "RUNN", "STOP": "STOP"}.get(state)
        self.querySFU(":TSGEN:CONF:COMM {}".format(state))
        time.sleep(2)
        res = self.getTsGenState()
        if res != check:
            return '****    Error: Wrong Playout State, Set = {}, Current = {}'.format(state, res)
        return res

    def getTsGenState(self):
        if not self.tsplayer: return 'TS player function not available'
        '''Returns the state of the transport stream player [STOP-PAUS-RUNN]'''
        return self.querySFU(":TSGEN:READ:COMM:STATE?")
    
    def setTsGenFile(self, tsFile):
        if not self.tsplayer: return 'TS player function not available'
        '''Sets the file for the transport stream player'''
        res = self.querySFU(":TSGEN:CONF:PLAY \"{}\";*WAI;:TSGEN:CONF:PLAY?".format(tsFile.replace('/', '\\')))
        errorCheck = self.getSystemError()
        if 'SFU check - Error' in errorCheck:
            return errorCheck
        return res
    
    def getTsGenFile(self):
        if not self.tsplayer: return 'TS player function not available'
        '''Returns the file loaded into the transport stream player'''
        return self.querySFU(":TSGEN:CONF:PLAY?")
        
    def setTsGenRate(self, rate):
        if not self.tsplayer: return 'TS player function not available'
        '''Sets the TS data rate in bit/s '''    
        return self.querySFU(":TSGEN:CONF:TSRATE {};*WAI;:TSGEN:CONF:TSRATE?".format(rate), str(rate))
    
    def getTsGenRate(self):
        if not self.tsplayer: return 'TS player function not available'
        '''Returns the TS data rate in bit/s'''
        return self.querySFU(":TSGEN:CONF:TSRATE?")
        
    def getTSGenWraps(self):
        if not self.tsplayer: return 'TS player function not available'
        '''Dektec Only
        Returns the number of playout wraps counted by the Dektec playout'''
        return self.querySFU(":TSGEN:CONF:WRAPS?")

    def getTSGenErrors(self):
        if not self.tsplayer: return 'TS player function not available'
        '''Dektec Only
        Returns the number of errors counted by the Dektec playout'''
        return self.querySFU(":TSGEN:CONF:ERRORS?")

#### Intrerfere Commands ##########################################################################
    def setInterfSource(self, interfSource):
        '''Sets up the interferer source
        [OFF | ARB=1 | DIG (I/Q digital) | ANA (I/Q analog) | ATV]'''
        return self.querySFU(":DM:ISRC {};*WAI;:DM:ISRC?".format(interfSource), interfSource)

    def getInterfSource(self):
        '''Returns the interferer source'''
        return self.querySFU(":DM:ISRC?")
        
    def setInterfType(self, interfType):
        '''Sets up the interferer type        [MNPR | BGPR | IPR | LPR]'''
        res = self.querySFU(":DM:IATV {};*WAI;:DM:IATV?".format(interfType), interfType)
        if '-222' in res:
            return '****    Error: This instrument does not have the {} feature'.format(interfType)
        return res

    def getInterfType(self):
        '''Returns the interferer type'''
        return self.querySFU(":DM:IATV?")
        
    def setInterfAtt(self, interfAtt):
        '''Sets up the interferer attenuation.
        Will only work interferer reference is set to attenuation.    interfAtt    -60.0 to 60.0'''
        # first, we need to know we are in attenuation mode
        interfAtt = str(interfAtt)
        if Decimal(interfAtt) < -60 or Decimal(interfAtt) > 60:
            return '****    Error: Interferer Attenuation out of range'
        res = self.querySFU("DM:IREF?")
        if 'SFU check - Error' in res:
            return res
        if 'LEV' in res:
            # we are in level mode so get out now
            return "****    Error: Interferer Reference set to Level"
        # right mode so carry on 
        return self.querySFU(":DM:IATT {};*WAI;:DM:IATT?".format(interfAtt), Decimal(interfAtt))

    def getInterfAtt(self):
        '''Returns the interferer attenuation'''
        return self.querySFU(":DM:IATT?")
            
    def setInterfFreq(self, interfFreq):
        '''Sets up the interferer frequency offset.        interfFreq    -40000000.0 to 40000000.0'''
        interfFreq = str(interfFreq)
        if Decimal(interfFreq) < -40000000 or Decimal(interfFreq) > 40000000:
            return '****    Error: Interferer Frequency out of range'
        return self.querySFU("DM:IFR {};*WAI;:DM:IFR?".format(interfFreq), Decimal(interfFreq))   

    def getInterfFreq(self):
        '''Returns the interferer frequency offset.'''
        return self.querySFU(":DM:IFR?")        

    def setInterfSigSour(self, signalSource):
        '''Sets the frequency offset of the useful signal in the baseband.    signalSourse    -10000000.0 to 10000000.0'''
        signalSource = str(signalSource)
        if Decimal(signalSource) < -40000000 or Decimal(signalSource) > 40000000:
            return '****    Error: Interferer Frequency Offset out of range'
        return self.querySFU(":DM:SFR {};*WAI;:DM:SFR?".format(signalSource), Decimal(signalSource))   

    def getInterfSigSour(self):
        '''Returns the interferer signal frequency offset'''
        return self.querySFU("DM:SFR?")

    def setInterfNoiseAdd(self, noise):
        '''Sets up the interferer added noise.
        noise    "BEFN" | "AFN" | "OFF"'''
        return self.querySFU(":DM:IADD {};*WAI;:DM:IADD?".format(noise), str(noise))
    
    def getInterfNoiseAdd(self):
        '''Returns the interferer added noise.'''
        return self.querySFU("DM:IADD?")

    def setInterfLevel(self, level):
        '''Sets the interferer level in dB.
        Will only work interferer reference is set to level.
        level    -110.0 to 10.0'''
        # first, we need to know we are in level mode
        level = str(level)
        if Decimal(level) < -110 or Decimal(level) > 10:
            return '****    Error: Interferer Level out of range'
        res = self.querySFU("DM:IREF?")
        if 'SFU check - Error' in res:
            return res
        if "ATT" in res:
            # we are in attenuation mode so get out now
            return "****    Error: Interferer Reference set to Attenuation"
        # right mode so carry on
        return self.querySFU(":DM:ILEV {};*WAI;:DM:ILEV?".format(level), Decimal(str(level)))

    def getInterfLevel(self):
        '''Returns the interferer level.'''
        return self.querySFU("DM:IREF?")

    def setInterfRef(self, ref):
        '''Sets up the interferer reference.        ref    "LEV" | "ATT"'''
        return self.querySFU(":DM:IREF {};*WAI;:DM:IREF?".format(ref), ref)

    def getInterfRef(self):
        '''Returns the interferer reference.'''
        return self.querySFU("DM:IREF?")
        
#### ARB Commands #################################################################################

    def setArb(self, state, arbFile): 
        if not self.arb: return 'ARB function not available'
        '''Sets the state of the ARB, and load a form if state is on.        state    "OFF" | "ON"        file     "filepath\filename'''
        return 'Arb File = {}, Arb State = {}'.format(self.setArbFile(arbFile), self.setArbState(state))
    
    def getArb(self):
        if not self.arb: return 'ARB function not available'
        '''Gets the state of the ARB        state    "OFF" | "ON"        file     "filepath\filename'''
        return 'Arb File = {}, Arb State = {}'.format(self.getArbFile(), self.getArbState())
    
    def setArbState(self, state):
        if not self.arb: return 'ARB function not available'
        '''Sets the state of the ARB
        state    "OFF" | "ON"'''   
        return self.querySFU(":BB:ARB:STAT {};*WAI;:BB:ARB:STAT?".format(state), state)

    def getArbState(self):
        if not self.arb: return 'ARB function not available'
        '''Returns the state of the ARB''' 
        return self.querySFU(":BB:ARB:STAT?")

    def setArbFile(self, fileName):
        if not self.arb: return 'ARB function not available' 
        '''Sets the ARB file.
        file    "filepath\filename'''
        saveTimeout = self.timeout
        self.timeout = 600
        if self.type == "SFU": 
            res = self.querySFU(":BB:ARB:WAV:SEL \"{}\";*WAI;:BB:ARB:WAV:SEL?".format(fileName.replace('/', '\\')))
            errorCheck = self.getSystemError()
            if 'SFU check - Error' in errorCheck:
                self.timeout = saveTimeout
                return errorCheck
        elif self.type == "Dektec": 
            self.writeSFU(":BB:ARB:WAV:SEL \"{}\";*WAI".format(fileName.replace('/', '\\')))
            time.sleep(2)
            res = self.getArbFile()            
        self.timeout = saveTimeout
        return res
    
    def getArbFile(self):
        if not self.arb: return 'ARB function not available' 
        '''Returns the ARB file'''
        if not self.arb:
            return 'N/A'
        return self.querySFU(":BB:ARB:WAV:SEL?")
    
    def setArbClock(self, freq):
        if not self.arb: return 'ARB function not available' 
        '''Sets the ARB clock outout rate frequency.        freq 400Hz to 100,000,000Hz (100MHz)'''  
        freq = str(freq)
        return self.querySFU(":BB:ARB:CLOC {};*WAI;:BB:ARB:CLOC?".format(freq), Decimal(freq))

    def getArbClock(self): 
        if not self.arb: return 'ARB function not available'
        '''Returns the ARB outout rate frequency'''  
        return self.querySFU(":BB:ARB:CLOC?")

    def setArbInterpol(self, inter):
        if not self.arb: return 'ARB function not available' 
        '''This setting is only applicable to a Dektec IQ mode modulator
        Options are OFDM interpolation or QAM interpolation'''    
        return self.querySFU(":BB:ARB:INTE {};*WAI:;BB:ARB:INTE?".format(inter), inter)

    def getArbInterpol(self):
        if not self.arb: return 'ARB function not available' 
        '''This setting is only applicable to a Dektec IQ mode modulator
        Options are OFDM interpolation or QAM interpolation'''
        return self.querySFU(":BB:ARB:INTE?")
    
    def setArbGain(self, gain):
        if not self.arb: return 'ARB function not available' 
        '''This setting is only applicable to a Dektec IQ mode modulator
        Options are OFDM interpolation or QAM interpolation''' 
        return self.querySFU(":BB:ARB:GAIN {};*WAI;:BB:ARB:GAIN?".format(gain), gain)
    
    def getArbGain(self):
        if not self.arb: return 'ARB function not available' 
        '''This setting is only applicable to a Dektec IQ mode modulator
        Returns the gain set of the IQ playout'''  
        return self.querySFU(":BB:ARB:GAIN?")

#### DVB Commands #################################################################################
    def setDvbtBand(self, bandwidth):
        '''Sets the DVB bandwidth    Valid = bandwidth    5 to 8'''
        bandwidth = "BW_{}".format(bandwidth)
        return self.querySFU(":DVBT:CHAN:BAND {};*WAI;:DVBT:CHAN:BAND?".format(bandwidth), bandwidth)  

    def getDvbtBand(self):
        '''Returns the DVB bandwidth'''
        return self.querySFU(":DVBT:CHAN:BAND?")    

    def setDvbtFft(self, mode):
        '''Sets the DVB FFT mode.        mode    2 | 4 | 8'''
        fft = "M{}K".format(mode)
        return self.querySFU(":DVBT:FFT:MODE {};*WAI;:DVBT:FFT:MODE?".format(fft), str(fft))
    
    def getDvbtFft(self):
        '''Returns the DVB FFT mode'''
        return self.querySFU(":DVBT:FFT:MODE?")

    def setDvbtGuard(self, guard):
        '''Sets the DVB guard mode 
        guard    4 | 8 | 16 | 32'''
        gi = "G1_{}".format(guard)
        return self.querySFU(":DVBT:GUAR:INT {};*WAI;:DVBT:GUAR:INT?".format(gi), gi[:4])   # only returns 4 charaters

    def getDvbtGuard(self):
        '''Returns the DVB guard'''
        return self.querySFU(":DVBT:GUAR:INT?")

    def setDvbtCons(self, const):
        '''Sets the DVB constellation  
        const    4 | 16 | 64'''
        con = "T{}".format(const)
        return self.querySFU(":DVBT:CONS {};*WAI;:DVBT:CONS?".format(con), str(con))

    def getDvbtCons(self):
        '''Returns the DVB constellation'''
        return self.querySFU(":DVBT:CONS?")

    def setDvbtCoderate(self, codeRate):
        '''Sets the DVB code rate [
        codeRate    "1_2" | "2_3" | "3_4" | "5_6" | "7_8"'''
        cr = "R{}".format(codeRate)
        return self.querySFU(":DVBT:RATE {};*WAI;:DVBT:RATE?".format(cr), str(cr))

    def getDvbtCoderate(self):
        '''Returns the DVB code rate'''
        return self.querySFU(":DVBT:RATE?")        
        
    def setDvbtUsedBand(self, bandwidth):
        '''Sets the DVB-t used bandwidth.    bandwidth        1,000,000.0 to 10,000,000.0'''
        bandwidth = str(bandwidth)
        return self.querySFU(":DVBT:USED:BAND {};*WAI;:DVBT:USED:BAND?".format(bandwidth), Decimal(bandwidth))

    def getDvbtUsedBand(self):
        '''Returns the DVB used bandwidth'''
        return self.querySFU(":DVBT:USED:BAND?")

    def setDvbtHierarchy(self, hMode):
        '''Sets the DVB-t DVBT hierarchical mode.
        Modes NONH, A1, A2 and A4'''
        hMode = (hMode, "NONH")[hMode == "NO"]
        return self.querySFU(":DVBT:HIER {};*WAI;:DVBT:HIER?".format(hMode), hMode)

    def getDvbtHierarchy(self):
        '''Returns the DVBT hierarchical mode'''
        return self.querySFU(":DVBT:HIER?")

    def setDvbtLpCoderate(self, codeRate):
        '''Sets the DVB LP code rate [
        codeRate    "1_2" | "2_3" | "3_4" | "5_6" | "7_8"'''
        cr = "R{}".format(codeRate)
        return self.querySFU(":DVBT:RATE:LOW {};*WAI;:DVBT:RATE:LOW?".format(cr), cr)
        
    def getDvbtLpCoderate(self):
        '''Returns the DVB LP code rate'''
        return self.querySFU(":DVBT:RATE:LOW?")        
        
    def setDvbtSource(self, source):
        '''Set the DVB-T input signal source.
        source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":DVBT:SOUR {};*WAI;:DVBT:SOUR?".format(source), str(source))

    def getDvbtSource(self):
        '''Returns the DVB-T input signal source.'''
        return self.querySFU(":DVBT:SOUR?")
 
    def setDvbtLpSource(self, source):
        '''Set the DVB-T LP input signal source.
        source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":DVBT:SOUR:LOW {};*WAI;:DVBT:SOUR:LOW?".format(source), str(source))

    def getDvbtLpSource(self):
        '''Returns the DVB-T LP input signal source.'''
        return self.querySFU(":DVBT:SOUR:LOW?")

#### ISDBT Commands ###############################################################################
    def setIsdbSystem(self, sys):
        '''Set the ISDBT system.        sys    "T" | "TSB1" | "TSB"]'''
        return self.querySFU(":ISDBt:SYSTem {};*WAI;:ISDBt:SYSTem?".format(sys), str(sys))

    def getIsdbSystem(self):
        '''Returns the ISDBT system.'''
        return self.querySFU(":ISDBt:SYSTem?")

    def setIsdbPortion(self, por):
        '''Set the ISDBT portion .
        por    "PDD" | "PDC" | "PCC" | "DDD" |"DDC" | "DCC" | "CCC"'''
        return self.querySFU(":ISDBt:PORTION {};*WAI;:ISDBt:PORTION?".format(por), str(por))

    def getIsdbPortion(self):
        '''Returns the ISDBT portion.'''
        return self.querySFU(":ISDBt:PORTION?")

    def setIsdbConst(self, layer, const):
        '''Set the ISDBT constellation for a selected layer.
        layer      "A" | "B" |"C"
        const      "DQ" | "QP" | "16" | "64"'''
        con = "C_{}".format(const)
        return self.querySFU(":ISDBt:CONStel:{0} {1};*WAI;:ISDBt:CONStel:{0}?".format(layer, con), con)

    def getIsdbConst(self, layer):
        '''Returns the ISDBT constellation for a selected layer.
        layer        "A" | "B" |"C"'''
        return self.querySFU(":ISDBt:CONStel:{}?".format(layer))

    def setIsdbSegment(self, layer, segment):
        '''Set the number of ISDBT segments for a selected layer.
        layer        "A" | "B" |"C"        segment      1 to 13'''
        return self.querySFU(":ISDBt:SEGMents:{0} {1};*WAI;:ISDBt:SEGMents:{0}?".format(layer, segment), int(segment))

    def getIsdbSegment(self, layer):
        '''Returns the number of ISDBT segments for a selected layer.
        layer        "A" | "B" |"C"'''
        return self.querySFU(":ISDBt:SEGMents:{}?".format(layer))
    
    def setIsdbCodeRate(self, layer, codeRate):
        '''Set the ISDBT code rate for a selected layer.
        layer        "A" | "B" |"C"
        coderate     "1_2" | "2_3" | "3_4" | "5_6" | "7_8"'''
        rate = "R{}".format(codeRate)
        return self.querySFU(":ISDBt:RATE:{0} {1};*WAI;:ISDBt:RATE:{0}?".format(layer, rate), rate)

    def getIsdbCodeRate(self, layer):
        '''Returns the ISDBT code rate for a selected layer.
        layer        "A" | "B" |"C"'''
        return self.querySFU(":ISDBt:RATE:{}?".format(layer))

    def setIsdbInter(self, layer, interleaver):
        '''Set the ISDBT interleaver for a selected layer.        layer        "A" | "B" |"C"    interlever    1 to 8'''
        return self.querySFU(":ISDBt:TIME:INT:{0} {1};*WAI;:ISDBt:TIME:INT:{0}?".format(layer, interleaver), interleaver)

    def getIsdbInter(self, layer):
        '''Returns the ISDBT interleaver for a selected layer.
        layer    "A" | "B" |"C"'''
        return self.querySFU(":ISDBt:TIME:INT:{}?".format(layer))

    def setIsdbFft(self, mode):
        '''Set the ISDBT FFT mode.        mode    "1_2" | "2_4" | "3_8"'''
        fft = "M{}K".format(mode)
        return self.querySFU(":ISDBt:FFT:MODE {};*WAI;:ISDBt:FFT:MODE?".format(fft), fft)

    def getIsdbFft(self):
        '''Returns the ISDBT FFT mode.'''
        return self.querySFU(":ISDBt:FFT:MODE?")

    def setIsdbGuard(self, guard):
        '''Set the ISDBT guard.
        guard    4 | 8 | 16 | 32'''
        gi = "G1_{}".format(guard)
        return self.querySFU(":ISDBt:GUARd {};*WAI;:ISDBt:GUARd?".format(gi), gi)

    def getIsdbGuard(self):
        '''Returns the ISDBT guard.'''
        return self.querySFU(":ISDBt:GUARd?")

    def setIsdbBandwidthVar(self, var):
        '''Set the ISDB-T Channel bandwidth variation.        var      -1000 to +1000'''
        if var >1000 or var <-1000:
            return "****    Sweep Points Set Error - Invalid Value for SFU {}    ****".format(var)
        return self.querySFU(":ISDBt:BAND:VAR {};:ISDBt:BAND:VAR?".format(var), var)

    def getIsdbBandwidthVar(self):
        '''Returns the ISDB-T Channel bandwidth variation.'''
        return self.querySFU(":ISDBt:BAND:VAR?")

    def setIsdbBandwidth(self, band):
        '''Set the ISDB-T Channel bandwidth.        band      6 | 7 | 8        valid = ["BW_8","BW_7","BW_6"]'''
        band = "BW_{}".format(band)
        return self.querySFU(":ISDBt:CHAN:BAND {};:ISDBt:CHAN:BAND?".format(band), band)

    def getIsdbBandwidth(self):
        '''Returns the ISDB-T Channel bandwidth.'''
        return self.querySFU(":ISDBt:CHAN:BAND?")

    def setIsdbSpecial(self, state):
        '''Sets the state of special settings.        state    "ON" | "OFF"'''
        return self.querySFU(":ISDBt:SPECial:SETTings:STAT {};*WAI;:ISDBt:SPECial:SETTings:STAT?".format(state), state)
  
    def getIsdbSpecial(self):
        '''Returns the state of the ISDBT special settings.'''   
        return self.querySFU(":ISDBt:SPECial:SETTings:STAT?")

    def setIsdbSpecSeg(self, segment, state):
        '''Sets the condition of the individual ISDBT segments.    Special settings must be on.
        segment    1 to 13        state      "ON" | "OFF" '''
        # These settings can not be querred    
        return self.querySFU(":ISDBt:SPECial:SEGM {},{};*WAI".format(segment, state))
  
#### DVB-C Commands ###############################################################################
    def setDvbcSource(self, source):
        '''Set the DVB-C input signal source.
        source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":DVBC:SOUR {};*WAI;:DVBC:SOUR?".format(source), source)

    def getDvbcSource(self):
        '''Returns the DVB-C input signal source.'''
        return self.querySFU(":DVBC:SOUR?")

    def setDvbcConst(self, const):
        '''Set the DVB-C constellation.
        const      16 | 32 | 64 | 128 | 256'''
        con = "C{}".format(const)
        return self.querySFU(":DVBC:CONS {};*WAI;:DVBC:CONS?".format(con), str(con))

    def getDvbcConst(self):
        '''Returns the DVB-C constellation.'''
        return self.querySFU(":DVBC:CONS?")
    
    def setDvbcSymbolRate(self, rate):
        '''Set the DVB-C symbol rate.        rate      0.1e6 to 8e6'''
        rate = str(rate)
        return self.querySFU(":DVBC:SYMB {};*WAI;:DVBC:SYMB?".format(rate), Decimal(rate))

    def getDvbcSymbolRate(self):
        '''Returns the DVB-C symbol rate.'''
        return self.querySFU(":DVBC:SYMB?")            
            
#### J.83/B Commands ##############################################################################
    def setJ83bSource(self, source):
        '''Set the J.83/B input signal source.
        source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":J83B:SOUR {};*WAI;:J83B:SOUR?".format(source), str(source))

    def getJ83bSource(self):
        '''Returns the J.83/B input signal source.'''
        return self.querySFU(":J83B:SOUR?")
    
    def setJ83bConst(self, const):
        '''Set the J.83/B constellation.
        const      64 | 256 | 1024'''
        con = "J{}".format(const)
        return self.querySFU(":J83B:CONS {};*WAI;:J83B:CONS?".format(con), con)

    def getJ83bConst(self):
        '''Returns the J.83/B constellation.'''
        return self.querySFU(":J83B:CONS?")
            
    def setJ83bSymbolRate(self, rate):
        '''Set the J.83/B symbol rate.    rate      4.824483e6 to 5.896591e6'''
        rate = str(rate)
        return self.querySFU(":J83B:SYMB {};*WAI;:J83B:SYMB?".format(rate), Decimal(rate))

    def getJ83bSymbolRate(self):
        '''Returns the J.83/B symbol rate.'''
        return self.querySFU(":J83B:SYMB?")
    
    def setJ83bInter(self, mode):
        '''Set the J.83/B interleaver.
        mode      0 to 12'''
        return self.querySFU(":J83B:INT:MODE {};*WAI;:J83B:INT:MODE?".format(mode), mode)

    def getJ83bInter(self):
        '''Returns the J.83/B interleaver.'''
        return self.querySFU(":J83B:INT:MODE?")

#### ATSC Commands ################################################################################
    def setAtscFreqRef(self, ref):
        '''Set the ATSC frequency reference to either
        pilot PIL or center CENT.'''
        #FREQ:VSBF PIL | CENT
        return self.querySFU(":FREQ:VSBF {};*WAI;:FREQ:VSBF?".format(ref), ref)

    def getAtscFreqRef(self):
        '''Returns tthe ATSC frequency reference.'''
        return self.querySFU(":FREQ:VSBF?")

#### DTMB / GB20600 Commands ######################################################################

    def setDtmbNetworkMode(self, mode):
        '''Set the DTMB network mode to either SFN or MFN.'''
        '''mode    "SFN" ("single frequency network)| "MFN (multi frequency network)"'''
        return self.querySFU(":DTMB:NETW {};:DTMB:NETW?".format(mode))

    def getDtmbNetworkMode(self):
        '''Returns the state of the DTMB network mode.'''
        return self.querySFU(":DTMB:NETW?")

    def setDtmbSingleMode(self, state):
        '''Set the DTMB single carrier mode to either on or off.        state    "ON" | "OFF or  "1 | 0"'''        
        return self.querySFU(":DTMB:SINGle {};*WAI;:DTMB:SINGle?".format(state), state)

    def getDtmbSingleMode(self):
        '''Returns the state of the DTMB single carrier mode.'''
        return self.querySFU(":DTMB:SINGle?")
    
    def setDtmbDualPilot(self, state):
        '''Set the DTMB Dual Pilot tone to either on or off.        state    "ON" | "OFF"'''
        return self.querySFU(":DTMB:DUAL:PILot {};*WAI;:DTMB:DUAL:PILot?".format(state), state)

    def getDtmbDualPilot(self):
        '''Returns the state of the DTMB Dual Pilot tone.'''
        return self.querySFU(":DTMB:DUAL:PILot?")

    def setDtmbConst(self, const):
        '''Set the DTMB constellation.        const      4 | 16 | 32 | 64 | 4NR        valid = ["D4","D16","D32","D32","D64","D4NR"]'''
        con = "D{}".format(const)
        return self.querySFU(":DTMB:CONS {};:DTMB:CONS?".format(con), con)

    def getDtmbConst(self):
        '''Returns the DTMB constellation.'''
        return self.querySFU(":DTMB:CONS?")
            
    def setDtmbCodeRate(self, rate):
        '''Set the DTMB code rate.        rate      0.4 | 0.6 | 0.8        valid = ["R04","R06","R08"]'''
        rate = "R0{}".format(rate.split('.')[1])
        return self.querySFU(":DTMB:RATE {};:DTMB:RATE?".format(rate), rate)

    def getDtmbCodeRate(self):
        '''Returns the DTMB Code rate.'''
        return self.querySFU(":DTMB:RATE?")

    def setDtmbGuard(self, guard):
        '''Set the DTMB Guard intervel.        rate      420 | 595 | 945        valid = ["G420","G595","G945"]'''
        guard = "G".format(guard)
        return self.querySFU(":DTMB:GUARD {};:DTMB:GUARD?".format(guard), guard)
    
    def getDtmbGuard(self):
        '''Returns the DTMB Guard intervel.'''
        return self.querySFU(":DTMB:GUARD?")

    def setDtmbInterleaver(self, inter):
        '''Set the DTMB time interleaver.        rate      OFF | 240 | 720        valid = ["OFF","I240","I720"]'''
        if inter != "OFF":
            inter = "I" + str(inter)
        return self.querySFU(":DTMB:TIME:INT {};*WAI;:DTMB:TIME:INT?".format(inter), inter)

    def getDtmbInterleaver(self):
        '''Returns the DTMB time interleaver.'''
        return self.querySFU(":DTMB:TIME:INT?")

    def setDtmbBandwidth(self, band):
        '''Set the DTMB Channel bandwidth.        band      8 | 7 | 6        valid = ["BW_8","BW_7","BW_6"]'''
        band = "BW_{}".format(band)
        return self.querySFU(":DTMB:CHAN:BAND {};*WAI;:DTMB:CHAN:BAND?".format(band), band)

    def getDtmbBandwidth(self):
        '''Returns the DTMB Channel bandwidth.'''
        return self.querySFU(":DTMB:CHAN:BAND?")

    def setDtmbSpecial(self, state):
        '''Set the DTMB special setting to on or off.        state    "ON" | "OFF"'''
        return self.querySFU(":DTMB:SETT {};*WAI;:DTMB:SETT?".format(state), state)

    def getDtmbSpecial(self):
        '''Returns the state of the DTMB special setting.'''
        return self.querySFU(":DTMB:SETT?")
    
    def setDtmbPowerBoost(self, state):
        '''Set the DTMB GI Power boost special setting to on or off.        state    "ON" | "OFF"'''
        return self.querySFU(":DTMB:SPEC:GIP {};*WAI;:DTMB:SPEC:GIP?".format(state), state)

    def getDtmbPowerBoost(self):
        '''Returns the state of the DTMB GI Power boost special setting.'''
        return self.querySFU(":DTMB:SPEC:GIP?")
        
    def setDtmbSiPowerNorm(self, state):
        '''Set the DTMB SI Power Normalization special setting to on or off.        state    "ON" | "OFF"'''
        return self.querySFU(":DTMB:SPEC:SIPN {};*WAI;:DTMB:SPEC:SIPN?".format(state), state)

    def getDtmbSiPowerNorm(self):
        '''Returns the state of the DTMB SI Power Normalization special setting.'''
        return self.querySFU(":DTMB:SPEC:SIPN?")
     
#READ COMMANDS DONT WORK        
#    def setDtmbCoChannelInt(self, state):
#        '''Set the DTMB Co-Channel Interferer special setting to on or off.'''
#
#        '''state    "ON" | "OFF"'''
#        cmd1 = ":DTMB:SPEC:CCI " + state + ""
#        cmd2 = ":DTMB:SPEC:CCI?"
#        if state == "OFF":
#            check = "0"
#        elif state == "ON":
#            check = "1"
#        else:
#            return cmd1 + "Set Error - Invalid value"
#        self.writeSFU(cmd1)
#        res = self.readSFU(cmd2)
#        if res.find("Error") != -1 or self.id == "Dummy":  return res
#        else:
#            if check == res:
#                mes = cmd1 + "_____     Ok     _____"
#            else:
#                mes = cmd1 + "Set Error"
#        return mes
#
#    def getDtmbCoChannelInt(self):
#        '''Returns the state of the DTMB Co-Channel Interferer special setting.'''
#        cmd1 = ":DTMB:SPEC:CCI?"
#        res = self.readSFU(cmd1)
#        return res

    def setDtmbGiPn(self, state):
        '''Set the DTMB Guard PN.
        state      VAR | CONS        valid = ["VAR","CONS"]
        XXXXXX Note: This remote command does not apear to be work within the SFU XXXXXX'''
        return self.querySFU(":DTMB:GIC {};*WAI;:DTMB:GIC?".format(state), state)

    def getDtmbGiPn(self):
        '''Returns the DTMB Guard PN.'''
        return self.querySFU(":DTMB:GIC?")

#DVB-T2 Commands
    def setT2FECFrame(self, *args):
        '''Set the DVB-T2 FEC Frame size.
        frame      NORM | SHOR        valid = ["NORM","SHOR"]
        plp        int'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        frame = args[0]
        return self.querySFU(":T2DV:PLP{0}:FECF {1};*WAI;:T2DV:PLP{0}:FECF?".format(plp, frame), str(frame))

    def getT2FECFrame(self, *args):
        '''Returns tthe DVB-T2 FEC Frame size.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:FECF?".format(plp))

    def setT2CodeRate(self, *args):
        '''Set the DVB-T2 code rate.
        rate      1_2 | 3_5 | 2_3 | 3_4 | 4_5 | 5_6        valid = ["R1_2","R3_5","R2_3","R3_4","R4_5","R5_6"]
        plp        int'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        rate = "R{}".format(args[0])
        return self.querySFU(":T2DV:PLP{0}:RATE {1};:T2DV:PLP{0}:RATE?".format(plp, rate), str(rate))

    def getT2CodeRate(self, *args):
        '''Returns the DVB-T2 Code rate.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:RATE?".fomrat(plp))

    def setT2Const(self, *args):
        '''Set the DVB-T2 constellation.
        const      4 | 16 | 64 | 256        valid = ["T4","T16","T64","T256"]
        plp        int'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        con = "T{}".format(args[0])
        return self.querySFU(":T2DV:PLP{0}:CONS {1};:T2DV:PLP{0}:CONS?".format(plp, con), con)

    def getT2Const(self, *args):
        '''Returns the DVB-T2 constellation.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:CONS?".format(plp))

    def setT2ConstRot(self, *args):
        '''Set the DVB-T2 constellation rotation to on or off.
        state    "ON" | "OFF
        plp        int"'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        state = str(args[0])
        return self.querySFU(":T2DV:PLP{0}:CROT {1};*WAI;:T2DV:PLP{0}:CROT?".format(plp, state), state)

    def getT2ConstRot(self, *args):
        '''Returns the state of the DVB-T2 constellation rotation setting.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:CROT?".format(plp))
    
    def setT2TimeIntType(self, *args):
        '''Set the state of the DVB-T2 time interval type setting.
        type       0 | 1        valid = ["0","1"]
        plp        int'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        intervalType = str(args[0])
        return self.querySFU(":T2DV:PLP{0}:TIL:TYPE {1};:T2DV:PLP{0}:TIL:TYPE?".format(plp, intervalType), intervalType)
    
    def getT2TimeIntType(self, *args):
        '''Returns the state of the DVB-T2 time interval type setting.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:TIL:TYPE?".format(plp))
    
    def setT2TimeIntFrame(self, *args):
        return "setT2TimeIntFrame not implmented"

    def getT2TimeIntFrame(self, *args):
        '''Returns the state of the DVB-T2 time interval frame setting.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:TIL:FINT?".format(plp))

    def setT2TimeIntLength(self, *args):
        '''Set the state of the DVB-T2 time interval length setting.
        type       0 - 255
        plp        int'''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        if int(args[0]) > 255: # or args[1] < 0:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:PLP{0}:TIL:LENG {1};:T2DV:PLP{0}TIL:LENG?".format(plp. args[0]), int(args[0]))

    def getT2TimeIntLength(self, *args):
        '''Returns the state of the DVB-T2 time interval length setting.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:TIL:LENG?".format(plp))
        
    def setT2DateNumBlock(self, *args):
        '''Set the value of the DVB-T2 PLP NUM BLOCKS
        Dektec only.
        '''
        plp = "1"
        if len(args) > 1:
            plp = str(args[1] +1)
        if int(args[0]) > 1023: # or args[1] < 0:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:PLP{0}:BLOC {1};:T2DV:PLP{0}:BLOC?".format(plp, args[0]), int(args[0]))

    def getT2DateNumBlock(self, *args):
        '''Returns the value of the DVB-T2 PLP NUM BLOCKS.'''
        plp = "1"
        if len(args) > 0:
            plp = str(args[0] +1)
        return self.querySFU(":T2DV:PLP{}:BLOC?".format(plp))
        
    def setT2Bandwidth(self, band):
        '''Set the DVB-T2 Channel bandwidth.
        band      2 (for 1.7) | 5 | 6 | 7 | 8 | 10        valid = ["BW_8","BW_7","BW_6","BW_5","BW_2","BW_10"]'''
        band = str(band)
        band = "BW_{}".format((band, "2")[Decimal(band) == 1.7])
        return self.querySFU(":T2DV:CHAN {};:T2DV:CHAN?".format(band), str(band))

    def getT2Bandwidth(self):
        '''Returns the DVB-T2 Channel bandwidth.'''
        return self.querySFU(":T2DV:CHAN?")
    
    def getT2UsedBandwidth(self):
        '''Returns the DVB-T2 usabale channel bandwidth.'''
        return self.querySFU(":T2DV:USED?")

    def setT2BandwidthVar(self, var):
        '''Set the DVB-T2 Channel bandwidth variation.
        var      -1000 to +1000'''
        if var >1000 or var <-1000:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:BAND:VAR {};:T2DV:BAND:VAR?".format(var), str(var))

    def getT2BandwidthVar(self):
        '''Returns the DVB-T2 Channel bandwidth variation.'''
        return self.querySFU(":T2DV:BAND:VAR?")    

    def setT2FFTSize(self, fft):
        '''Set the DVB-T2 FFT size.
        band      1K | 2K | 4K | 8K | 16K | 32K | 8E | 16E | 32E         valid = ["M1K","M2K","M4K","M8K","M16K","M32K","M8E","M16E","M32E"]'''
        fft = "M{}".format(fft)
        return self.querySFU(":T2DV:FFT:MODE {};:T2DV:FFT:MODE?".format(fft), fft)

    def getT2FFTSize(self):
        '''Returns the DVB-T2 FFT size.'''
        return self.querySFU(":T2DV:FFT:MODE?")
    
    def setT2Guard(self, guard):
        '''Set the DVB-T2 FFT size.
        band      1_4 | 1_8 | 1_16 | 1_32 | 1128 | 19128 | 19256         valid = ["G1_4","G1_8","G1_1","G1_3","G112","G191","G192"]'''
        guard = "G{:.3}".format(guard)
        return self.querySFU(":T2DV:GUAR:INT {};:T2DV:GUAR:INT?".format(guard), guard)
    
    def getT2Guard(self):
        '''Returns the guard interval.'''
        return self.querySFU(":T2DV:GUAR:INT?")

    def setT2PilotPat(self, pattern):
        '''Set the DVB-T2 pilot pattern.
        pattern      1 to 8         valid = ["PP1","PP2","PP3","PP4","PP5","PP6","PP7","PP8"]'''
        pattern = "PP{}".format(pattern)
        return self.querySFU(":T2DV:PIL {};:T2DV:PIL?".format(pattern), pattern)
    
    def getT2PilotPat(self):
        '''Returns the gDVB-T2 pilot pattern.'''
        return self.querySFU(":T2DV:PIL?")
    
    def setT2FramesPerSuper(self, frames):
        '''Set the number of T2 frames per super frame (N_T2).
        frames      2 to 255 '''
        if frames > 255 or frames < 2:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:NT2F {};:T2DV:NT2F?".format(frames), str(frames))

    def getT2FramesPerSuper(self):
        '''Returns the number of T2 frames per super frame (N_T2).'''
        return self.querySFU(":T2DV:NT2F?")
    
    def getT2OfdmPerFrame(self):
        '''Returns the number of OFDM symbols per T2 frame (L_f).
        Read only prameter'''
        return self.querySFU(":T2DV:LF?")
    
    def setT2DataPerFrame(self, symbols):
        '''Set the number of data symbols per T2 frame (L_DATA).
        symbols      3 to 2097 '''
        if int(symbols) > 2097 or int(symbols) < 3:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:LDAT {};:T2DV:LDAT?".format(symbols), int(symbols))
    
    def getT2DataPerFrame(self):
        '''Returns the number of data symbols per T2 frame (L_DATA).'''
        return self.querySFU(":T2DV:LDAT?")
    
    def setT2SlicesPerFrame(self, slices):
        '''Set the number of subslices per T2 frame (N_SUB).
        Slices      currently only 1 allowed '''
        if slices > 1 or slices < 1:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:NSUB {};:T2DV:NSUB?".format(slices), str(slices))
    
    def getT2SlicesPerFrame(self):
        '''Returns the number of subslices per T2 frame (N_SUB).'''
        return self.readSFU(":T2DV:NSUB?")

    def setT2NetworkMode(self, mode):
        '''Set the DVB-T2 network mode.
        pattern      MFN, SFN (only MFN implented)         valid = ["MFN","SFN"]'''
        return self.querySFU(":T2DV:NETW {};:T2DV:NETW?".format(mode), mode)
    
    def getT2NetworkMode(self):
        '''Returns the DVB-T2 newwotk mode.'''
        return self.readSFU(":T2DV:NETW?")

    def getT2TxSystem(self):
        '''Returns the DVB-T2 transmission system.'''
        return self.querySFU(":T2DV:TXSY?")
    
    def setT2TxSystem(self, system):
        return "setT2TxSystem not implmented"

    def setT2PAPR(self, state):
        '''Set the state of the DVB-T2 PAPR setting.
        state    "OFF" | "TR"  also ACE" | "ACE_TR" on the Dektec        valid = ["OFF","TR","ACE","ACE_TR"]'''   
        return self.querySFU(":T2DV:PAPR {};:T2DV:PAPR?".format(state), str(state))

    def getT2PAPR(self):
        '''Returns the state of the DVB-T2 time PAPR setting.'''
        return self.querySFU(":T2DV:PAPR?")

    def setT2FEF(self, state):
        return "getT2FEF not implmented"

    def getT2FEF(self):
        '''Returns the state of the DVB-T2 time FEF setting.'''
        return self.querySFU(":T2DV:FEF?")
    
    def setT2TFS(self, state):
        return "setT2TFS not implmented"

    def getT2TFS(self):
        '''Returns the state of the DVB-T2 time TFS setting.'''
        return self.querySFU(":T2DV:TFS?")
    
    def setT2L1T2Version(self, version):
        '''Set the state of the DVB-T2 L2T2 version.
        version    "V111" | "V121"        valid = ["V111","V121"]'''   
        return self.querySFU(":T2DV:L:T2V {};:T2DV:L:T2V?".format(version), version)

    def getT2L1T2Version(self):
        '''Returns the state of the DVB-T2 L1T2 version.'''
        return self.querySFU(":T2DV:L:T2V?")    
    
    def setT2L1PostMod(self, mod):
        '''Set the state of the DVB-T2 L1 post modulation.
        version    "2" | "4" | "16" | "64"        valid = ["T2","T4","T16","T64"]'''   
        mod = "T" + str(mod)
        return self.querySFU(":T2DV:L:CONS {};:T2DV:L:CONS?".format(mod), mod)

    def getT2L1PostMod(self):
        '''Returns the state of the DVB-T2 L1 post modulation.'''
        return self.querySFU(":T2DV:L:CONS?")
    
    def setT2L1Repetition(self, state):
        '''Set the state of the DVB-T2 L1 repetition setting.        state    "OFF" | "ON"        valid = ["OFF","ON"]'''   
        return self.querySFU(":T2DV:L:REP {};*WAI;:T2DV:L:REP?".format(state), state)
    
    def getT2L1Repetition(self):
        '''Returns the state of the DVB-T2 time PAPR setting.'''
        return self.querySFU(":T2DV:L:REP?")

    def setT2L1PostExtension(self, state):
        return "setT2L1PostExtension not implmented"

    def getT2L1PostExtension(self):
        '''Returns the state of the DVB-T2 L1 post extension setting.'''
        return self.querySFU(":T2DV:L:EXT?")
    
    def setT2NumAuxStream(self, num):
        return "setT2NumAuxStream not implmented"

    def getT2NumAuxStream(self):
        '''Returns the state of the DVB-T2 time TFS setting.'''
        return self.querySFU(":T2DV:NAUX?")
    
    def getT2L1RfSignalling(self):
        '''Returns the state of the DVB-T2 L1 RF Signalling.'''
        return self.querySFU(":T2DV:L:RFS?")    
    
    def setT2CellId(self, cellId):
        '''Set the value of the cell id setting. Value set by remote commands is
        an integer but value displayed on SFU screen is a hex value.    id    0 to 65,535'''
        if id > 65535 or id < 0:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:ID:CELL {};:T2DV:ID:CELL?".format(cellId), str(cellId))
    
    def getT2CellId(self):
        '''Returns the value of the cell id setting. Values returned by the
        remote commands are integer values of hex numbers displayed on the
         SFU screen.'''
        return self.querySFU(":T2DV:ID:CELL?")
    
    def setT2NetworkId(self, netId):
        '''Set the value of the network id setting. Value set by remote commands is
        an integer but value displayed on SFU screen is a hex value.    id    0 to 65,535'''
        if id > 65535 or id < 0:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:ID:NETW {};:T2DV:ID:NETW?".format(netId), str(netId))
    
    def getT2NetworkId(self):
        '''Returns the value of the network id setting. Values returned by the
        remote commands are integer values of hex numbers displayed on theb SFU screen.'''
        return self.querySFU(":T2DV:ID:NETW?")
    
    def setT2SystemId(self, sysId):
        '''Set the value of the system id setting. Value set by remote commands is
        an integer but value displayed on SFU screen is a hex value.    id    0 to 65,535'''
        if id > 65535 or id < 0:
            return "Set Error - Invalid value"
        return self.querySFU(":T2DV:ID:T2SY {};:T2DV:ID:T2SY?".format(sysId), str(sysId))
    
    def getT2SystemId(self):
        '''Returns the value of the system id setting. Values returned by the
        remote commands are integer values of hex numbers displayed on the SFU screen.'''
        return self.querySFU(":T2DV:ID:T2SY?")

    def setT2MIInterface(self, state):
        '''Set the state of the DVB-T2 MI Modulator Interface.    state    "OFF" | "ON"        valid = ["OFF","ON"]'''   
        return self.querySFU(":T2DV:INPUT:T2MI:INT {};*WAI;:T2DV:INPUT:T2MI:INT?".format(state), state)
    
    def getT2MIInterface(self):
        '''Returns the state of the DVB-T2 MI Modulator Interface.'''
        return self.querySFU(":T2DV:INPUT:T2MI:INT?")

    def setT2MISource(self, source):
        '''Set the source of the DVB-T2 MI Modulator Interface stream.
        state    "INTERNAL" | "EXTERNAL"        valid = ["INTERNAL","EXTERNAL"]'''   
        return self.querySFU(":T2DV:INPUT:T2MI:SOUR {};:T2DV:INPUT:T2MI:SOUR?".format(source), source)
    
    def getT2MIsetT2MISource(self):
        '''Returns the source of the DVB-T2 MI Modulator Interface stream.'''
        return self.querySFU(":T2DV:INPUT:T2MI:SOUR?")
        
    def setT2EFEPayload(self, source):
        '''Set the type of the DVB-T2 FEF Payload type.
        state    "NULL" | "NOIS"        valid = ["NULL","NOIS"]'''
        return self.querySFU(":T2DV:FEF:PAYL {};*WAI;:T2DV:FEF:PAYL?".format(source), source)

    def getT2EFEPayload(self):
        '''Returns the type of the DVB-T2 FEF Payload type.'''
        return self.querySFU(":T2DV:FEF:PAYL?")

    def setT2BBMode(self, bbmode):
        '''Set the type of the DVB-T2 BB mode used per PLP.
        state    "HEM High Effincy Mode" | "NOIS Normal Mode"
        Note to set PLP 0 use PLP1, PLP 1 uese PLP2 etc        valid = ["HEM","NM"]'''   
        return self.querySFU(":T2DV:PLP1:BB_M {};*WAI;:T2DV:PLP1:BB_M?".format(bbmode), str(bbmode))

    def getT2BBMode(self):
        '''Returns the type of the DVB-T2 BB Mode set.'''
        return self.querySFU(":T2DV:PLP1:BB_M?")
        
    def setT2MIpidId(self, pid):
        ''' Sets the PID of the stream to be played within the the T2MI stream'''
        #pid = '#H' + pid
        return self.querySFU(":T2DV:INP:T2MI:PID {};*WAI;:T2DV:INP:T2MI:PID?".format(pid), str(pid))
    
    def getT2MIpidId(self):
        ''' Sets the PID of the stream to be played within the the T2MI stream'''
        #pid = '#H' + pid
        return self.querySFU(":T2DV:INP:T2MI:PID?")
        
    def setT2MIsidId(self, sid):
        ''' Sets the SID of the stream to be played within the the T2MI stream'''
        return self.querySFU(":T2DV:INP:T2MI:SID {};*WAI;:T2DV:INP:T2MI:SID?".format(sid), str(sid))  
    
    def getT2MIsidId(self):
        ''' Sets the SID of the stream to be played within the the T2MI stream'''
        return self.querySFU(":T2DV:INP:T2MI:SID?")  
    ### DVBS    
    
    def setDvbsSource(self, source):
        if not self.dvbs: return 'DVBS function not available'
        '''Set the DVB-S input signal source.    source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":DVBS:SOUR {};:DVBS:SOUR?".format(source), source)
    
    def getDvbsSource(self):
        if not self.dvbs: return 'DVBS function not available'
        '''Returns the DVB-S input signal source.'''
        return self.querySFU(":DVBS:SOUR?")
    
    def setDvbsConst(self, const):
        if not self.dvbs: return 'DVBS function not available'
        '''Set the DVBS constellation.
        4 | 8 |16        valid = ["S4","S8","S16"]'''
        con = "S{}".format(const)
        if self.type == "Dektec":
            return con
        return self.querySFU(":DVBS:CONS {};:DVBS:CONS?".format(con), con)

    def getDvbsConst(self):
        if not self.dvbs: return 'DVBS function not available'
        '''Returns the DVBS constellation.'''
        return self.querySFU(":DVBS:CONS?")
    
    def setDvbsSymbolRate(self, rate):
        if not self.dvbs: return 'DVBS function not available'
        '''Set the DVB-S symbol rate.    rate      0.100 to 100.000 MS/s'''
        return self.querySFU(":DVBS:SYMB {};:DVBS:SYMB?".format(rate), str(rate))

    def getDvbsSymbolRate(self):
        if not self.dvbs: return 'DVBS function not available'
        '''Returns the DVB-S symbol rate.'''
        return self.querySFU(":DVBS:SYMB?")

    def setDvbsCoderate(self, codeRate):
        if not self.dvbs: return 'DVBS function not available'
        '''Sets the DVB-S code rate [
        codeRate    "R1_2" | "R2_3" | "R3_4" | "R5_6" | "R7_8" | R8_9"        valid = ["R1_2", "R2_3", "R3_4", "R5_6", "R7_8", "R8_9"]'''
        cr = "R" + codeRate
        return self.querySFU(":DVBS:RATE {};*WAI;:DVBS:RATE?".format(cr), cr)

    def getDvbsCoderate(self):
        if not self.dvbs: return 'DVBS function not available'
        '''Returns the DVB-S code rate'''
        return self.querySFU(":DVBS:RATE?")
    
    def setDvbsRollOff(self, rollOff):
        if not self.dvbs: return 'DVBS function not available'
        '''Sets the DVB-S value of roll off        rollOff    "0.25" | "0.3" | "0.35" | "0.4" | "0.45"        valid = ["0.25", "0.3", "0.30", "0.35", "0.4", "0.40", "0.45"]'''
        return self.querySFU(":DVBS:ROLL {};:DVBS:ROLL?".format(rollOff), str(rollOff))

    def getDvbsRollOff(self):
        if not self.dvbs: return 'DVBS function not available'
        '''Returns the DVB-S value of roll off'''
        return self.querySFU(":DVBS:ROLL?")

    def setDvbsInputSignal(self, inputSig):
        if not self.dvbs: return 'DVBS function not available'
        '''Sets the DVB-S input signal source [
        codeRate    "EXT" | "TSP" | "TEST"        valid = ["EXT", "TSP", "TEST"]'''
        return self.querySFU(":DVBS:SOUR {};:DVBS:SOUR?".format(inputSig), inputSig)
    ### DVBS2
    
    def setDvbs2Source(self, source):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Set the DVB-S2 input signal source.
        source      "EXT" | "TSPL" | "TEST"'''
        return self.querySFU(":DVBS2:SOUR {};:DVBS2:SOUR?".format(source), source)

    def getDvbs2Source(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 input signal source.'''
        return self.querySFU(":DVBS2:SOUR?")    
    
    def setDvbs2Const(self, const):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Set the DVBS2 constellation.
        4 | 8 |16 | 32
        S2X only
        S4VL | S2VL | S2SVL | A8L | A16L | A32L | A64 | A64L | A128 | A256 | A256L | SL3
        valid = ["S4", "S8", "A16", "A32", "S4VL", "S2VL", "S2SVL", "A8L", "A16L", "A32L",
        "A64", "A64L", "A128", "A256", "A256L" , "SL3"]'''
        con = {"4": "S4", "8": "S8", "16": "A16", "32": "A32"}.get(str(const), str(const))
        return self.querySFU(":DVBS2:CONS {};*WAI;:DVBS2:CONS?".format(con), str(con))

    def getDvbs2Const(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVBS2 constellation.'''
        return self.querySFU(":DVBS2:CONS?")
    
    def setDvbs2SymbolRate(self, rate):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Set the DVB-S2 symbol rate.    rate      1.000 to 45.000 MS/s'''
        rate = str(rate)
        return self.querySFU(":DVBS2:SYMB {};*WAI;:DVBS2:SYMB?".format(rate), Decimal(rate))

    def getDvbs2SymbolRate(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 symbol rate.'''
        return self.querySFU(":DVBS2:SYMB?")
    
    def setDvbs2Coderate(self, codeRate):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Sets the DVB-S2 code rate [        
        codeRate    "1_4" | "1_3" | "2_5" | "1_2" | "3_5" | "2_3" 
        | "3_4" | "4_5" |"5_6" | "6_7" | "7_8" 1 "8_9" | "9_10"
        S2X only
        "R2_9" | "R11_45" | "R4_15" | "R13_45" | "R14_45" | "R9_20" | "R7_15" |
        "R8_15" | "R11_20" | "R5_9" | "R26_45" | "R28_45" | "R23_36" | "R29_45" |
        "R31_45" | "R25_36" | "R32_45" | "R13_18" | "R11_15" | "R7_9" | "R77_90"
        valid = ["R1_4", "R1_3", "R2_5", "R1_2", "R3_5", "R2_3", "R3_4", "R4_5", "R5_6", "R6_7", "R7_8", "R8_9", "R9_1",
        "R2_9", "R11_45", "R4_15", "R13_45", "R14_45", "R9_20", "R7_15", "R8_15", "R11_20", "R5_9", "R26_45", "R28_45",
        "R23_36", "R29_45", "R31_45", "R25_36", "R32_45", "R13_18", "R11_15", "R7_9", "R77_90"]
        '''
        cr = "R{}".format(codeRate)
        if cr == "R9_10":
            cr = "R9_1"
        return self.querySFU(":DVBS2:RATE {};*WAI;:DVBS2:RATE?".format(cr), cr)

    def getDvbs2Coderate(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 code rate'''
        return self.querySFU(":DVBS2:RATE?")
    
    def setDvbs2FecFrame(self, state):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Sets the DVB-S2 FEC frame length condition        NORMAL for 64800 bit | SHORT for 16200 bit        valid = ["NORMAL", "SHORT"]'''
        state = ("SHOR", "NORM")[state == "NORMAL"]
        return self.querySFU(":DVBS2:FECF {};:DVBS2:FECF?".format(state), state)

    def getDvbs2FecFrame(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 FEC frame length condition
        NORMAL for 64800 bit | SHORT for 16200 bit'''
        return self.querySFU(":DVBS2:FECF?")
    
    def setDvbs2Pilots(self, state):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Sets the DVB-S2 Pilots state to ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU(":DVBS2:PIL {};*WAI;:DVBS2:PIL?".format(state), state)
        
    def getDvbs2Pilots(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 Pilots state        ON | OFF'''
        return self.querySFU(":DVBS2:PIL?")
    
    def setDvbs2RollOff(self, rollOff):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Sets the DVB-S2 value of roll off
        rollOff    0.05 | 0.1 | 0.15 | 0.2 | 0.25 | 0.35        valid = ["0.05", "0.1", "0.10", "0.15", "0.2", "0.20", "0.25", "0.35"]"'''
        rollOff = str(rollOff)
        return self.querySFU(":DVBS2:ROLL {};*WAI;:DVBS2:ROLL?".format(rollOff), Decimal(rollOff))        
    
    def getDvbs2RollOff(self):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Returns the DVB-S2 Rolloff value
        0.05 | 0.1 | 0.15 | 0.2 | 0.25 | 0.35'''
        return self.querySFU(":DVBS2:ROLL?")

    def setDvbs2InputSignal(self, inputSig):
        if not self.dvbs2: return 'DVBS2 function not available'
        '''Sets the DVB-S2 input signal source [        codeRate    "EXT" | "TSP" | "TEST"'''
        return self.querySFU(":DVBS2:SOUR {};*WAI;:DVBS2:SOUR?".format(inputSig), inputSig)

############################################################################################################
    #Analog TV    
    def setAtvVideoSource(self, source):
        ''' Sets the Video input signal source to either External or Video Generator    "EXT" | "VGEN" '''
        return self.querySFU("RATV:VID:VINP {};*WAI;:RATV:VID:VINP?".format(source), source)
    
    def getAtvVideoSource(self):
        ''' Gets the Video input signal source'''
        return self.querySFU("RATV:VID:VINP?")
    
    def setAtvVisionPicture(self, picture):
        '''Sets the vision picture of a gernerated video
        "C75P" | "C75N" | "C75S" | "FUBP" | "CPAM" | "CPAN" | "LIBRary"         valid = ["C75P", "C75N", "C75S", "FUBP", "CPAM", "CPAN", "LIBRary"]'''
        return self.querySFU("RATV:VIDG:VIS {};:RATV:VIDG:VIS?".format(picture), picture)
    
    def getAtvVisionPicture(self):
        '''Gets the vision picture beeing generated'''
        return self.querySFU("RATV:VIDG:VIS?")
    
    def setAtvLoadVisionPicture(self, patternFile):
        '''Loads additional test patten file from the ATV video libray.
        Only valid if FROM ATV VIDEO LIB has been selected as the vision picture opton'''
        cmd1 = "RATV:VIDG:LIBR:SEL  \"{}\";*WAI".format(patternFile)
        self.querySFU(cmd1)
        time.sleep(5)  
        return "ATV test pattern loaded"   
        
    def setAtvAudioSource(self, source):
        ''' Sets the Audio input signal source to either External, Audio Generator
        or Audio Player        "EXT" | "AGEN" | "APL"        valid = ["EXT", "AGEN", "APL"]'''
        return self.querySFU("RATV:AUD:AINP {};*WAI;:RATV:AUD:AINP?".format(source), source)
    
    def getAtvAudioSource(self):
        ''' Gets the Audio input signal source'''
        return self.querySFU("RATV:AUD:AINP?")
    
    def setAtvAudioExtZ(self, impedance):
        '''Selects the input impedance of the external audio input. 
        50 ohms (Z50) or 600 ohms (Z600)        valid = ["Z50", "Z600"]'''
        return self.querySFU("RATV:AUEX:IMP {};*WAI;:RATV:AUEX:IMP?".format(impedance), str(impedance))
    
    def getAtvAudioExtZ(self):
        ''' Gets the value of the input impedance of the external audio input'''
        return self.querySFU("RATV:AUEX:IMP?")
    
    def setAtvAudioState(self, channel, state):
        '''Sets the state of the audio channel 1 or 2 on (ON) or off (OFF).    valid1 = ["ON", "OFF"]'''
        return self.querySFU("RATV:AUDG:AUD:AF{0} {1};*WAI;:RATV:AUDG:AUD:AF{0}?".format(channel, state), state)
    
    def getAtvAudioState(self, channel):
        ''' Gets the state of the audio channel 1 or 2'''
        return self.querySFU("RATV:AUDG:AUD:AF{}?".format(channel))
    
    def setAtvAudioFrequency(self, channel, frequency):
        '''Sets the AF frequency of the MONO/CH1/LEFT* sound signal (Ch 1) or 
        AF frequency of the CH2/RIGHT* sound signal (Ch 2)
        frequency = 30 Hz to 15000 Hz'''
        frequency = str(frequency)
        if str(channel) not in ["1", "2"]:
            return "****    Error: - Invalid value"
        return self.querySFU("RATV:AUDG:AUD:FRQ{0} {1};*WAI;;RATV:AUDG:AUD:FRQ{0}?".format(channel, frequency), Decimal(frequency))
    
    def getAtvAudioFrequency(self, channel):
        ''' Gets the value of the AF frequency of the MONO/CH1/LEFT* sound signal (Ch 1) or 
        AF frequency of the CH2/RIGHT* sound signal (Ch 2)'''
        return self.querySFU("RATV:AUDG:AUD:FRQ{}?".format(channel))

    def setAtvAudioLevel(self, channel, level):
        '''Sets the AF level of the MONO/CH1/LEFT* sound signal (Ch 1) or 
        AF frequency of the CH2/RIGHT* sound signal (Ch 2)
        level = -60 dBu to +12 dBu'''
        if str(channel) not in ["1", "2"]:
            return "****    Error - Invalid value"
        return self.readSFU("RATV:AUDG:AUD:LEV{0} {1};*WAI;:RATV:AUDG:AUD:LEV{0}?".format(channel, level), str(level))
    
    def getAtvAudioLevel(self, channel):
        ''' Gets the value of the AF level of the MONO/CH1/LEFT* sound signal (Ch 1) or 
        AF frequency of the CH2/RIGHT* sound signal (Ch 2)'''
        return self.querySFU("RATV:AUDG:AUD:LEV{}?".format(channel))
        
    def setAtvLoadAudioPlayer(self, audioFile):
        '''Selects the audio player file. If the file is not in the default path, 
        the path must be specified at the same time. If no file of the specified name 
        exists, it is created. The file extension may be omitted. Only files with the 
        file extension *.wv will be created or loaded'''
        cmd1 = "RATV:APL:LIBR:SEL  \"{}\";*OPC?".format(audioFile)
        self.querySFU(cmd1)
        time.sleep(3)    
        return "Audio player file loaded"   
    
    def setAtvSoundMode(self, mode):
        ''' Sets the Audio sound mode
        off (OFF), FM mono modulation (FMM), FM stereo modulation (FMST), FM dual-sound (FMD) 
        FM stereo Korea (FMSK), FM dual-sound Korea (FMDK), BTSC mono modulation (BTSC), 
        NICAM modulation (NIC), AM modulation (AMM), and analog sound plus NICAM modulation (MNIC)'''
        if mode not in ["OFF", "FMM", "FMST", "FMD", "FMSK", "FMDK","BTSC", "NIC", "AMM", "MNIC"]:
            return "****    Error: Invalid value"
        return self.querySFU("RATV:SOUN:MODE {};*WAI;:RATV:SOUN:MODE?".format(mode), mode)
    
    def getAtvSoundMode(self):
        ''' Gets the Audio sound mode'''
        return self.querySFU("RATV:SOUN:MODE?")
    
    def setAtvSoundNicam(self, mode):
        '''Sets the NICAM modulation signal        Stereo 1 (STE1), Dual 1 (DUA1) or Mono 1 (MON1) etc'''
        if mode not in ["STE1", "STE2", "STE3", "STE4", "DUA1", "DUA2", "DUA3", "DUA4", "MON1", "MON2", "MON3", "MON4"]:
            return "****    Error: NICAM modulation signal Invalid value"
        return self.querySFU("RATV:SOUN:NICS {};*WAI;:RATV:SOUN:NICS?".format(mode), mode)
    
    def getAtvSoundNicam(self):
        ''' Gets the NICAM modulation signal'''
        return self.querySFU("RATV:SOUN:NICS?")
    
    def setAtvSpecialState(self, state):
        '''Sets the overall state of the special settings.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:SETT:STAT {};:RATV:SPEC:SETT:STAT?".format(state), state)
    
    def getAtvSpecialState(self):
        ''' Gets the overall state of the special settings'''
        return self.querySFU("RATV:SPEC:SETT:STAT?")
    
    def setAtvSpecialAMDepth(self, depth):
        '''If special settings is on, sets  the modulation depth of the L standard 
        amplitude-modulated sound.
        0 to 100%'''
        return self.querySFU("RATV:SPEC:SOUN:AMD {};*WAI;:RATV:SPEC:SOUN:AMD?".format(depth), str(depth))
    
    def getAtvSpecialAMDepth(self):
        ''' Gets the modulation depth of the L standard 
        amplitude-modulated sound'''
        return self.querySFU("RATV:SPEC:SOUN:AMD?")
    
    def setAtvSpecialFrqDeviation(self, subcarrier, frequency):
        '''If special settings is on, sets the frequency deviation of sound subcarrier 1 or 2         20000 Hz to 75000 Hz.'''
        frequency = str(frequency)
        return self.querySFU("RATV:SPEC:SOUN:DEV{0} {1};*WAI;:RATV:SPEC:SOUN:DEV{0}?".format(subcarrier, frequency), Decimal(frequency))
    
    def getAtvSpecialFrqDeviation(self, subcarrier):
        ''' Gets the the frequency deviation of sound subcarrier 1 or 2 amplitude-modulated sound'''
        return self.querySFU("RATV:SPEC:SOUN:DEV{}?".format(subcarrier))
    
    def setAtvSpecialFrqDeviationPilot(self, frequency):
        '''If special settings is on, sets the frequency deviation of the pilot carrier on sound subcarrier 2
        1000 Hz to 4000 Hz.'''
        frequency = str(frequency)
        return self.querySFU("RATV:SPEC:SOUN:DEVP {};*WAI;:RATV:SPEC:SOUN:DEVP?".format(frequency), Decimal(frequency))
    
    def getAtvSpecialFrqDeviationPilot(self):
        ''' Gets the the frequency deviation of the pilot carrier on sound subcarrier 2 
        amplitude-modulated sound'''
        return self.querySFU("RATV:SPEC:SOUN:DEVP?")
    
    def setAtvSpecialSubFrequency(self, subcarrier, frequency):
        '''If special settings is on, sets the RF frequency of sound subcarrier 1 or 2.
        subcarrier = 1 | 2         frequency  = 4000000 Hz to 7000000 Hz.'''
        frequency = str(frequency)
        return self.querySFU("RATV:SPEC:SOUN:FRQ{0} {1};*WAI;:RATV:SPEC:SOUN:FRQ{0}?".format(subcarrier, frequency), Decimal(frequency))
    
    def getAtvSpecialSubFrequency(self, subcarrier):
        ''' Gets the RF frequency of sound subcarrier 1 or 2. 
        amplitude-modulated sound        subcarrier = 1 | 2 '''
        return self.querySFU("RATV:SPEC:SOUN:FRQ{}?".format(subcarrier))
    
    def setAtvSpecialSubLevel(self, subcarrier, level):
        '''If special settings is on, sets the level of sound subcarrier 1/of the MONO sound subcarrier 
        or sound subcarrier 2. The level is referenced to the vision carrier sync pulse (0 dB).
        subcarrier = 1 | 2 level = -34.0 dB to -4.0 dB.'''
        level = str(level)
        return self.querySFU("RATV:SPEC:SOUN:LEV{0} {1};*WAI;:RATV:SPEC:SOUN:LEV{0}?".format(subcarrier, level), Decimal(level))
    
    def getAtvSpecialSubLevel(self, subcarrier):
        ''' Gets the level of sound subcarrier 1/of the MONO sound subcarrier 
        or sound subcarrier 2. The level is referenced to the vision carrier sync pulse (0 dB).
        subcarrier = 1 | 2 '''
        return self.querySFU("RATV:SPEC:SOUN:LEV{}?".format(subcarrier))
    
    def setAtvSpecialPilotState(self, state):
        '''Sets the state of the pilot carrier on sound subcarrier 2 ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:SOUN:PIL {};*WAI;:RATV:SPEC:SOUN:PIL?".format(state), state)
    
    def getAtvSpecialPilotState(self):
        ''' Gets the state of tpilot carrier on sound subcarrier 2 ON or OFF'''
        return self.querySFU("RATV:SPEC:SOUN:PIL?")
    
    def setAtvSpecialPreemphasis(self, preemphasis):
        '''Sets the preemphasis for the AF sound channels.
        PREEMPHASIS OFF, PREEMPHASIS 50 s and PREEMPHASIS 75 s'''
        preemphasis = ('D'.format(preemphasis), preemphasis)[preemphasis == 'OFF']
        if preemphasis not in ["OFF", "D50", "D75"]:
            return '****    Error: Preemphasis Invalid value'
        return self.querySFU("RATV:SPEC:SOUN:PRE {};*WAI;:RATV:SPEC:SOUN:PRE?".format(preemphasis), preemphasis)
    
    def getAtvSpecialPreemphasis(self):
        ''' Gets the preemphasis for the AF sound channels.'''
        return self.querySFU("RATV:SPEC:SOUN:PRE?")
    
    def setAtvSpecialSubState(self, subcarrier, state):
        '''Sets the state of the  sound subcarrier 1/the MONO sound subcarrier or sound subcarrier 2 ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:SOUN:SUB{0} {1};*WAI;:RATV:SPEC:SOUN:SUB{0}?".format(subcarrier, state), state)
    
    def getAtvSpecialSubState(self, subcarrier):
        ''' Gets the state of the  sound subcarrier 1/the MONO sound subcarrier or sound subcarrier 2 ON or OFF,'''
        return self.querySFU("RATV:SPEC:SOUN:SUB {}?".format(subcarrier))
    
    def setAtvSpecialVisionCarrier(self, state):
        '''Sets the state of the  vision carrier ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:TRP:CARR {};*WAI;:RATV:SPEC:TRP:CARR?".format(state), state)
    
    def getAtvSpecialVisionCarrier(self):
        ''' Gets the state of  vision carrier ON or OFF.'''
        return self.querySFU("RATV:SPEC:TRP:CARR?")
    
    def setAtvSpecialGDPrecorrection(self, state):
        '''Sets the state of the video group delay precorrection ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:TRP:GDPR {};*WAI;:RATV:SPEC:TRP:GDPR?".format(state), state)
    
    def getAtvSpecialGDPrecorrection(self):
        ''' Gets the state of the video group delay precorrection ON or OFF'''
        return self.querySFU("RATV:SPEC:TRP:GDPR?")
    
    def setAtvSpecialResidualCarrier(self, percent):
        '''Sets the amount of residual carrier.        Residual carrier  = 0.0 % to 30.0 %'''
        percent = str(percent)
        return self.querySFU("RATV:SPEC:TRP:RES {};*WAI;:RATV:SPEC:TRP:RES?".format(percent), Decimal(percent))
    
    def getAtvSpecialResidualCarrier(self):
        ''' Gets the amount of residual carrier.'''
        return self.querySFU("RATV:SPEC:TRP:RES?")
    
    def setAtvSpecialVideoSignal(self, state):
        '''Sets the state of the video signal ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:TRP:VID {};*WAI;:RATV:SPEC:TRP:VID?".format(state), state)
    
    def getAtvSpecialVideoSignal(self):
        ''' Gets the state of the video signal ON or OFF.'''
        return self.querySFU("RATV:SPEC:TRP:VID?")
    
    def setAtvSpecialVSBFilter(self, state):
        '''Sets the state of the vestigial sideband filter ON or OFF.        valid = ["ON", "OFF"]'''
        return self.querySFU("RATV:SPEC:TRP:VSBF {};*WAI;:RATV:SPEC:TRP:VSBF?".format(state), state)
    
    def getAtvSpecialVSBFilter(self):
        ''' Gets the state of the vestigial sideband filter ON or OFF.'''
        return self.querySFU("RATV:SPEC:TRP:VSBF?")
    
    def setAtvSpecialVSBCharact(self, char):
        '''Sets the state of the vestigial sideband filter ON or OFF.
        B/G standard (BG), I standard (I and I1), D/K standard (D/K NICAM, D/K FM and D/K), 
        M/N standard (M and N) and L standard (L and L NIC)
        char = BG|BGAustralia|I|I1|DKNicam|DKFM|DK|M|N|L|LNICam                valid = ["BG", "BGA", "I", "I1", "DKN", "DKFM", "DK", "M", "N", "L", "LNIC"]'''
        return self.querySFU("RATV:SPEC:TRP:VSBC {};*WAI;:RATV:SPEC:TRP:VSBC?".format(char), str(char))
    
    def getAtvSpecialVSBCharact(self):
        ''' Gets the state of the vestigial sideband filter ON or OFF.'''
        return self.querySFU("RATV:SPEC:TRP:VSBC?")  

##### BER Tester Commands #############
    def setBerMeasState(self, state):
        '''Starts BER measurement or halts it.'''
        return self.querySFU(":SENS:BER:MEAS {};*WAI;:SENS:BER:MEAS?".format(state), state)

    def getBerMeasState(self):
        '''Returns the status of BER measurement'''
        return self.querySFU(":SENS:BER:MEAS?")

    def setBerMeasRestart(self):
        '''Restarts BER measurement.'''
        return self.querySFU(":SENSe:BER:REST;*OPC?")

    def setBerInput(self, berInput):
        '''Selects the input used for BER measurement.'''
        berInput = {"ASI1": "ASIF", "ASI2":"ASIR", "SMP1":"SMPF", "SMP2":"SMPR"}.get(berInput)
        if berInput not in ["SER", "ASIF", "ASI1", "ASIR", "ASI2", "SPIF", "SPIR", "SMPF", "SMP1", "SMPR", "SMP2"]:
            return '****    Error: - Invalid BER input value'
        return self.querySFU(":SENS:BER:INP:SEL {};*WAI;:SENS:BER:INP:SEL?".format(berInput), berInput)

    def getBerInput(self):
        '''Returns the current of BER input'''
        return self.querySFU(":SENS:BER:INP:SEL?")

    def setBerSignal(self, signal):
        '''Selects the type of packeted data stream if using MPEG transport stream inputs.        valid = ["H184", "S187", "H200", "S203", "H204", "S207", "STUF"]'''
        return self.querySFU(":SENSe:BER:SIGN {};*WAI;:SENSe:BER:SIGN?".format(signal), str(signal))

    def getBerSignal(self):
        '''Returns the type of packeted data stream if using MPEG transport stream inputs.'''
        return self.querySFU("SENSe:BER:SIGN?")

    def getBerRead(self):
        '''Returns the instantaneously measured bit error rate.'''
        return self.querySFU(":READ:BER?")

    def getBerReadAll(self):
        '''Queries the bit error rate and other parameters.'''
        return self.querySFU(":READ:BER:ALL?")

    def getBerEval(self):
        '''Indicates the progress of BER measurement as two numeric values: the first is the currently evaluated number of bits, 
        while the second specifies the number of bits needed to be evaluated to produce the required measurement accuracy.'''
        return self.querySFU(":READ:BER:EVAL?")

    def getBerState(self):
        '''Displays the current status of the bit error rate meter.
        A status message with a higher priority will cover a status message with a lower priority.'''
        return self.querySFU(":READ:BER:STAT?")

    def getBerErrorCount(self):
        '''Returns the sum of bit errors to date as a numeric value.'''
        return self.querySFU(":READ:BER:COUN?")

    def setBerGateMode(self, mode):
        '''Selects the gating mode.        valid = ["AUT", "INF", "UWIN", "USIN"]'''
        return self.querySFU(":SENS:BER:GATE:MODE {};*WAI;:SENS:BER:GATE:MODE?".format(mode), str(mode))

    def getBerGateMode(self):
        '''Returns the gating mode.'''
        return self.querySFU(":SENS:BER:GATE:MODE?")

    def getBerGateTime(self):
        ''' Returns the gating time'''
        return self.querySFU(":READ:BER:GATE:TIME?")
        
    def setBerPayload(self, mode):
        '''Selects the payload contents of the received packets.        valid = ["PRBS", "H00", "HFF"]'''
        return self.querySFU(":SENS:BER:PAYL {};*WAI;:SENS:BER:PAYL?".format(mode), str(mode))

    def getBerPayload(self):
        '''Returns the payload contents of the received packets..'''
        return self.querySFU(":SENS:BER:PAYL?")
    
    def setBerPrbs(self, mode):
        '''Selects the PRBS sequency.    valid = ["P15_", "P23_"]'''
        return self.querySFU(":SENS:BER:PRBS:SEQ {}_;*WAI;:SENS:BER:PRBS:SEQ?".format(mode), "{}_".format(mode))
    
    def getBerPrbs(self):
        '''Returns the PRBS sequency.'''
        return self.querySFU(":SENS:BER:PRBS:SEQ?")    
    
    def setDektecT2Group(self, groupRef):
        '''Selects the group name and verifies the group reference.'''

        # DigitalTVLabs
        if groupRef[0:4] == "DTVL":
            groupName = "DigitalTVLabs"
            groupRefNumber = int(groupRef[4:])
            if groupRefNumber < 1 or groupRefNumber > 59 :
                return "{}:{} Set Error - Invalid reference".format(groupName, groupRef)
            
        # DTG_DBook_7_0
        elif groupRef[0:3] == "DTG":
            groupName = "DTG_DBook_7_0"
            groupRefNumber = int(groupRef[3:])
            if groupRefNumber < 0 or groupRefNumber > 207 :
                return "{}:{} Set Error - Invalid reference".format(groupName, groupRef)

        # Teracom
        elif groupRef[0:4] in ["VHF1", "VHF2", "UHF1", "UHF2", "UHF3"]:
            groupName = "Teracom"

        # VV0xx
        elif groupRef[0:3] == "VV0":
            groupName = "VV0xx"
            valid = ["VV001-CR35",    "VV003-CR23",
                     "VV004-8KFFT",   "VV005-8KFFT",   "VV006-16KFFT",  "VV007-16KFFT", "VV008-16KFFT", "VV009-4KFFT",   "VV010-2KFFT", "VV011-1KFFT",
                     "VV012-64QAM45", "VV013-64QAM56", "VV014-64QAM34", "VV015-8KFFT",  "VV016-256QAM34",
                     "VV017-PAPRTR",  "VV018-MISO",    "VV019-NOROT",   "VV020-FEF",
                     "VV034-DTG016",  "VV035-DTG052",  "VV036-DTG091",  "VV037-DTG167", "VV038-DTG168" ]
            if groupRef not in valid:
                return "{} Set Error - Invalid reference".format(groupRef)

        # VV1xx
        elif groupRef[0:3] == "VV1":
            groupName = "VV1xx"
            groupRefNumber = int(groupRef[3:])
            if groupRefNumber < 0 or groupRefNumber > 30 :
                return "{}:{} Set Error - Invalid reference".format(groupName, groupRef)

        # VV2xx
        elif groupRef[0:3] == "VV2":
            groupName = "VV2xx"
            groupRefNumber = int(groupRef[3:])
            if groupRefNumber < 0 or groupRefNumber > 61 :
                return "{}:{} Set Error - Invalid reference".format(groupName, groupRef)

        # VV3xx
        elif groupRef[0:3] == "VV3":
            groupName = "VV3xx"
            groupRefNumber = int(groupRef[3:])
            if groupRefNumber < 0 or groupRefNumber > 83 :
                return "{}:{} Set Error - Invalid reference".format(groupName, groupRef)
            
        else:
            return "{} Set Error - Invalid reference".format(groupRef)

        return self.readSFU(":DEKTEC:T2:GROUP {}/{};:DEKTEC:T2:GROUP?".format(groupName, groupRef), groupRef)
    
    def getDektecT2Group(self):
        '''Return the group reference '''
        return self.readSFU(":DEKTEC:T2:GROUP?")