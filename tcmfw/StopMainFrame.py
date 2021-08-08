# -*- coding: utf-8 -*-
# The MIT License
#
# Copyright (c) 2018 Aaron Greenyer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
    tcm.py
    ~~~~~~~~~~~

    Test Control Manager to create an application that sets up and runs test scripts.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import wx
import time
import os
import sys
import StopMainFrameBase
from loguru import logger


# Implementing MyFrame2
class StopMainFrame( StopMainFrameBase.MyFrame2 ):
    def __init__( self, parent ):
        StopMainFrameBase.MyFrame2.__init__( self, parent )
        self.stopFile  = 'stop.txt'
        self.stopNextFile  = 'stopNext.txt'
        self.stopLastFile  = 'stopLast.txt'
        self.pauseFile = 'pause.txt'
        self.copyFlagFile = 'copyFlag.txt'
        self.updateStatus = ''
        t = time.ctime(time.time())
        self.updateStatus = 'script started at ' + t       
        self.m_textCtrl3.SetValue(self.updateStatus)
        TIMER_ID = 100
        self.timer = wx.Timer(self, TIMER_ID) 
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer) 
        self.timer.Start(milliseconds=3000, oneShot=False)
        # creat default copyFileFlag
        try:
            #print 'Create copyFlag file'
            f = open(self.copyFlagFile, 'w+')
            junk = 'copyFlagFile created'
            f.write(junk)
            f.close() 
        except:
            logger.warning('copyFlag File error')
    
    def OnCloseFrame(self, event):
        try:
            fs = open(self.stopFile, 'w+')
        except:
            logger.warning('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopFile + '\n')
            return False
        t = time.ctime(time.time())
        self.updateStatus = 'script stop flag created at ' + t      
        self.m_textCtrl3.SetValue(self.updateStatus)
        fs.write(self.updateStatus)
        fs.close()
        sys.exit(0)
        
    # Handlers for MyFrame2 events.
    ########################################################################################
    # Closes the script control GUI
    def OnExit( self, event ):
        try:
            fs = open(self.stopFile, 'w+')
        except:
            logger.warning('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopFile + '\n')
            return False
        t = time.ctime(time.time())
        self.updateStatus = 'script stop flag created at ' + t      
        self.m_textCtrl3.SetValue(self.updateStatus)
        fs.write(self.updateStatus)
        fs.close()
        sys.exit(0)
    
    
    #########################################################################################
    # Set the stopNext file to .txt and delete the .tx file.
    # Test script should detect stopNext.txt file, stop the script before the start of the 
    # next test and rename stop.txt to stop.tx and set the .tx file.
    def OnNext( self, event ):
        try:
            fs = open(self.stopNextFile, 'w+')
        except:
            logger.warning('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopFile + '\n')
            return False
        t = time.ctime(time.time())
        self.updateStatus = 'script stop before next test flag created at ' + t       
        self.m_textCtrl3.SetValue(self.updateStatus)
        fs.write(self.updateStatus)
        fs.close()    
    
    
    #########################################################################################
    # Set the stopLast file to .txt and delete the .tx file.
    # Test script should detect stopLast.txt file, stop the script before the start of the 
    # next group of tests and rename stop.txt to stop.tx and set the .tx file.
    def OnLast( self, event ):
        try:
            fs = open(self.stopLastFile, 'w+')
        except:
            logger.warning('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopLastFile + '\n')
            return False
        t = time.ctime(time.time())
        self.updateStatus = 'script stop last test in this group flag created at ' + t     
        self.m_textCtrl3.SetValue(self.updateStatus)
        fs.write(self.updateStatus)
        fs.close()    
    
    
    
    
    #########################################################################################
    # Set the stop file to .txt and delete the .tx file.
    # Test script should detect stop.txt file, stop the script and rename stop.txt to stop.tx
    # and set the .tx file.
    def OnStop( self, event ):
        try:
            fs = open(self.stopFile, 'w+')
        except:
            logger.warning('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopFile + '\n')
            return False
        t = time.ctime(time.time())
        self.updateStatus = 'script stop flag created at ' + t      
        self.m_textCtrl3.SetValue(self.updateStatus)
        fs.write(self.updateStatus)
        fs.close()
        sys.exit(0)
    
     
    #############################################################################################
    # Test script should detect pause.txt file and halt the script until the pause.txt is deleted
    # and set the .tx file.    
    def OnPause( self, event ):
        try:
            f = open(self.pauseFile, 'w+')
        except:
            logger.warning('StopMainFrame.py pauseFunction ERROR: cannot create ' + self.pauseFile + '\n')
            return False
        
        self.m_button4.Enable(False)
        self.m_button5.Enable(True)
        t = time.ctime(time.time())
        self.updateStatus = 'script paused at ' + t
        self.m_textCtrl3.SetValue(self.updateStatus)
        f.write(self.updateStatus)
        f.close()


    #############################################################################################
    # Test script should detect pause.txt file and halt the script until the pause.txt is deleted
    # and set the .tx file.    
    def OnResume( self, event ):
        try:
            os.remove(self.pauseFile) # delete the pause file
        except:
            logger.warning('StopMainFrame.py resumeFunction ERROR: failed to delete pause file')
            return False
        
        self.m_button4.Enable(True)
        self.m_button5.Enable(False)
        t = time.ctime(time.time())
        self.updateStatus = 'script resumed at ' + t
        self.m_textCtrl3.SetValue(self.updateStatus)
        
        
    #############################################################################################    
    def OnTimer(self, evt):
        try:
            inFile = open('commsfile.txt', 'r') # open GUI communications file for read
            inField = inFile.readline()
            inText =  inFile.readline()
            #print 'commsfile inField = ' + inField + '   inText = ' + inText + '\n'
            self.m_textCtrl2.SetValue(inText)
            inFile.close() # close read file
            if inText.find('USER') != -1:
                newText = inText.replace('USER', 'user')
                self.OnPause(evt) # user input required, so call Pause function
                inFile = open('commsfile.txt', 'w') # open GUI communications file for write
                inFile.write(inField)
                inFile.write(newText)
                inFile.close() # close write file
        except Exception as e:
            pass#print(f'GUI OnTimer ERROR {e}')
    
    ###############################################################################################
    def boxChanged( self, event ):
        print('tick box changed')
        try:
            if self.m_checkBox1.GetValue() == True:
                print('Create copyFlag file')
                f = open(self.copyFlagFile, 'w+')
                junk = 'copyFlagFile created'
                f.write(junk)
                f.close() 
            else:
                print('Delete copyFlag file')
                if os.path.exists(self.copyFlagFile):
                    os.remove(self.copyFlagFile)
        except:
            logger.warning('copyFlag File error')
    
#######################################################################################################################
#######################################################################################################################

class Main(wx.App):
    def OnInit(self):
        self.m_frame = StopMainFrame(None)
        self.m_frame.Show()
        self.SetTopWindow(self.m_frame)
        return True

app = Main(0)
app.MainLoop()
