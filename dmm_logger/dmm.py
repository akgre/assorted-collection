'''
Reading from a DMM to measure the maximum readout rate
'''
#import os
import time
import numpy as np 
import matplotlib.pyplot as plt  
import signal
from decimal import Decimal
import logging
import log_test
from pymeasure.instruments import Instrument
    
FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")

log_test.do_something()
logging.getLogger().handlers.clear()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.handlers.clear()
'''c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
log.addHandler(c_handler)'''

#logtesting = logging.getLogger('pyVISA')
#logtesting.handlers.clear()
#c_handler = logging.StreamHandler()
#c_handler.setLevel(logging.DEBUG)
#logtesting.addHandler(c_handler)

#log_test.do_something()

class EndMe:
    '''
    I am a doc string
    '''
    finish_him = False
    def __init__(self):
        '''
        I am a doc string
        '''
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        '''
        I am a doc string
        '''
        self.finish_him = True

    def i_am_here_for_fun(self):
        '''
        I'm here to get rid of an error message.
        '''
        self.finish_him = True

class DmmDataManager:
    '''
    I am a doc string
    '''
    def __init__(self):
        '''
        I am a doc string
        '''
        self.list_smpl_cnt = []
        self.all_data = []
        self.start_time = 0
        self.total_time = 0
        
    def dmm_time_convert(self, dmm_time):
        '''
            convert the time from the DMM
        '''
        list_of_time = dmm_time.strip().split(',')
        hours = Decimal(list_of_time[0])*60*60
        minutes = Decimal(list_of_time[1])*60
        seconds = Decimal(list_of_time[2])
        dmm_time_seconds = hours + minutes + seconds
        return dmm_time_seconds

    def begin_time(self, dmm_time):
        '''
        record the start time
        '''
        self.total_time = 0
        self.start_time = self.dmm_time_convert(dmm_time)

    def current_run_time(self, dmm_time):
        '''
        record the total time from the start
        '''
        self.total_time = self.dmm_time_convert(dmm_time) - self.start_time

    def add_data(self, raw_data):
        '''
        append the new data to the current data
        '''
        index_num = raw_data[1]
        data_samples = raw_data[int(index_num)+2:].strip().split(',')
        self.list_smpl_cnt.append(len(data_samples))
        for sample_point in data_samples:
            self.all_data.append(sample_point)

    def sample_rate(self):
        '''
        calculate the sample rate
        '''
        if Decimal(self.total_time) > 0:
            return sum(self.list_smpl_cnt)/Decimal(self.total_time)
        else:
            return Decimal('1')

    def display_data(self):
        '''
        display the info about the data rate, total time and number of samples
        '''
        log.info('')
        log.info('total time = {:.2f}'.format(self.total_time))
        log.info('sample count = {}'.format(sum(self.list_smpl_cnt)))
        log.info('average sample rate = {:.2f}sps'.format(self.sample_rate()))
        log.info('average sample time = {:.6f}ms'.format(Decimal('1000')/self.sample_rate()))
        log.info('')
     
    def interpolate_data(self):
        '''
        display the info about the data rate, total time and number of samples
        '''
        data_points = int(round((1/self.sample_rate())/Decimal('0.0001')))
        log.info('points factor = %s' % data_points)
        interpolate_data = list(np.repeat(self.all_data, data_points))
        return interpolate_data

class DMMLogging:
    '''
    DMM logging class
    '''
    def __init__(self):
        self.DMM = Instrument("TCPIP0::10.45.26.149::hislip0::INSTR", 'DMM', timeout=10000)
        #self.FGEN = e_cnrtl.EthernetControl("10.45.26.154", 5025, 18)
        self.FINISH_READING = EndMe()
        self.DMM_DATA = DmmDataManager()

    def setup(self, *args, **kwargs):
        '''
        sets up the dmm
        '''
        nplc = kwargs.get('nplc', '1')
        sample_count = kwargs.get('sample_count', '1000000')
        trigger_count = kwargs.get('trigger_count', '1')
        trigger_delay = kwargs.get('trigger_delay', '0.000091')
        
        setup_dict = {}
        for setting in ('nplc', 'sample_count', 'trigger_count', 'trigger_delay'):
            setup_dict[setting] = locals()[setting]
            log.info('Setting: %s = %s' % (setting, setup_dict[setting]))
        
        #FGEN.ask("SOUR1:FREQ 1000 HZ;*OPC?")
        #FGEN.ask("SOUR1:VOLT 1 VPP;*OPC?")
        #FGEN.ask(":OUTP1 ON;*OPC?")
        log.info('ID = %s' % self.DMM.id)
        self.DMM.ask("*RST;*WAI;*CLS;*OPC?")
        self.DMM.ask(":DISP:STAT OFF;:CONF:VOLT:DC 1,1;"
                ":SENS:VOLT:DC:RANG 1;*OPC?")
        self.DMM.ask(":SENS:VOLT:DC:NULL:VAL:AUTO OFF;"
                ":SENS:VOLT:DC:ZERO:AUTO ONCE;*OPC?")
        self.DMM.ask(":VOLTage:DC:IMPedance:AUTO OFF;"
                ":SAMP:COUN {};*OPC?".format(sample_count))
        self.DMM.ask(":TRIG:SOUR BUS;:TRIG:COUN {};"
                ":TRIG:DEL {};*OPC?".format(trigger_count, trigger_delay)) #:AUTO ON / 0.000092
        log.info('NPLC = %s' % self.DMM.ask(":SENS:VOLT:DC:NPLC {};:SENS:VOLT:DC:NPLC?".format(nplc)))
        log.info('Error = %s' % self.DMM.ask("SYST:ERROR?"))
        
    def run(self, run_time=60, print_rate=1):
        '''
        collects the data from the dmm and records the start and stop time.
        '''
        self.DMM.ask("R?")
        #freq = decimal.Decimal('999.3478')
        #fcount = decimal.Decimal('0')
        #FGEN.ask("SOUR1:FREQ {} HZ;*OPC?".format(freq))
        log.info(self.DMM.ask("DATA:POIN?"))
        self.DMM.write("INIT")
        time.sleep(1)
        self.DMM.write("*TRG")
        self.DMM_DATA.begin_time(self.DMM.ask("SYSTem:TIME?"))
        print_time = time.time()
        test_time_start = Decimal(str(time.time()))
        log.info('Starting Measurment Loop\n')
        while(Decimal(str(time.time())) - test_time_start < run_time) and (not self.FINISH_READING.finish_him):
            num_of_samples = self.DMM.ask("DATA:POIN?")
            #FGEN.ask("SOUR1:FREQ {} HZ;*OPC?".format(freq+fcount))
            #fcount += decimal.Decimal('0.000001')
            if int(num_of_samples) < 1:
                time.sleep(1)
                #self.DMM_DATA.current_run_time()
                continue
            self.DMM_DATA.add_data(self.DMM.ask("R?"))
            self.DMM_DATA.current_run_time(self.DMM.ask("SYSTem:TIME?"))
            if time.time()-print_time > print_rate:
                #log.info('freq = {}, {}'.format(freq+fcount, decimal.Decimal(FGEN.ask("SOUR1:FREQ?"))-freq-fcount+decimal.Decimal('0.000001')))
                print_time = time.time()
                self.DMM_DATA.display_data()
        fout = open("dmm_data.csv", "w")
        time_index = 0
        self.DMM_DATA.display_data()
        for sample in self.DMM_DATA.interpolate_data():
            fout.writelines('{:0.6f};{}\n'.format(time_index, sample))
            time_index += 1/(sum(self.DMM_DATA.list_smpl_cnt)/Decimal(self.DMM_DATA.total_time))
        fout.close()
        return ()

    def wrap_up(self):
        '''
        displays the final result for the application
        '''
        sample_count = sum(self.DMM_DATA.list_smpl_cnt)
        total_time = self.DMM_DATA.total_time
        pred_sr = 1/(Decimal('0.0006086564306184857266366736579196')+Decimal('0.0003')+Decimal('0.000091'))
        if total_time == 0:
            return
        log.info('\n\n\n\n\n\n\n')
        log.info('total time = {:.2f}'.format(total_time))
        log.info('average sample rate = {:.2f}, {:.6f}'.format(sample_count/Decimal(total_time), self.DMM_DATA.sample_rate()))
        log.info('Predited sample rate = {:.6f}, Diff = {:.6f}'.format(pred_sr, pred_sr-self.DMM_DATA.sample_rate()))
        log.info('average sample time = {:.6f}'.format(1/self.DMM_DATA.sample_rate()))
        log.info('\n\n\n\n\n\n\n')
        # Compute the x and y coordinates for points on a sine curve
        sample_num = (20000, sum(self.DMM_DATA.list_smpl_cnt))[sum(self.DMM_DATA.list_smpl_cnt) < 20000]
        log.info(sample_num)
        x = np.arange(0, sample_num, 1) 
        #print(x)
        #print(DMM_DATA.all_data[:100])
        y = np.asarray(self.DMM_DATA.all_data[:len(x)], dtype=np.float)
        #lt.title("sine wave form") 

        # Plot the points using matplotlib 
        plt.plot(x, y) 
        plt.show() 

def main():
    '''
    main program. will run a setup, the main task then wrap up the results.
    '''
    log.info('Program has started')
    logging_test = DMMLogging()
    nplc_time_dict = {'100': 2, '10': 0.2, '1': 0.02, '0.2': 0.003, '0.02': 0.0003} #   This is just a reminder of how many seconds a sample takes. this does not count for other delays
    logging_test.setup(nplc = '10', sample_count = '1000000', trigger_delay = '0.000091') # set up DMM
    logging_test.run(10, 2)    # Run test
    logging_test.wrap_up()      # Display results from test

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.warning("terminated")
    except Exception as error_message:
        log.info(error_message)
        raise