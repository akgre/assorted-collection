# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Aug 25 2009)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import string
import platform
import os

###########################################################################
## Class MyFrame2
###########################################################################

class MyFrame2 ( wx.Frame ):
    
    def __init__( self, parent ):
        winVer = platform.release()
        location = os.getcwd()
        #print winVer
        if winVer.find('XP') != -1:
            #print 'Windows XP'
            wx.Frame.__init__  ( self, parent, id = wx.ID_ANY, title = u"Script control: " + location, pos = wx.DefaultPosition, size = wx.Size( 435,210 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )#
        else:
            #print 'Not Windows XP'
            wx.Frame.__init__  ( self, parent, id = wx.ID_ANY, title = u"Script control: " + location, pos = wx.DefaultPosition, size = wx.Size( 435,232 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )#    
        
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        
        bSizer8 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer4 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_textCtrl3 = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 410,-1 ), wx.TE_READONLY )
        bSizer4.Add( self.m_textCtrl3, 0, wx.ALL, 5 )
        
        self.m_panel21 = wx.Panel( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL )
        bSizer9 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_staticText1 = wx.StaticText( self.m_panel21, wx.ID_ANY, u"Current test", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )
        bSizer9.Add( self.m_staticText1, 0, wx.ALL, 5 )
        
        self.m_textCtrl2 = wx.TextCtrl( self.m_panel21, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 405,-1 ), wx.TE_READONLY )
        bSizer9.Add( self.m_textCtrl2, 0, wx.ALL, 5 )
        
        self.m_panel21.SetSizer( bSizer9 )
        self.m_panel21.Layout()
        bSizer9.Fit( self.m_panel21 )
        bSizer4.Add( self.m_panel21, 1, wx.EXPAND |wx.ALL, 5 )
        
        bSizer10 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer81 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_button2 = wx.Button( self.m_panel2, wx.ID_ANY, u"E&xit", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer81.Add( self.m_button2, 0, wx.ALL, 5 )
        
        bSizer10.Add( bSizer81, 0, wx.EXPAND, 5 )
        
        bSizer91 = wx.BoxSizer( wx.VERTICAL )
        
        bSizer10.Add( bSizer91, 1, wx.EXPAND, 5 )
        
        bSizer7 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_button3 = wx.Button( self.m_panel2, wx.ID_ANY, u"&Stop", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button3.SetBackgroundColour( wx.Colour( 255, 128, 128 ) )
        
        bSizer7.Add( self.m_button3, 0, wx.ALL, 5 )
        
        self.m_button51 = wx.Button( self.m_panel2, wx.ID_ANY, u"Stop &Next", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer7.Add( self.m_button51, 0, wx.ALL, 5 )
        
        self.m_button6 = wx.Button( self.m_panel2, wx.ID_ANY, u"Stop &Last", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer7.Add( self.m_button6, 0, wx.ALL, 5 )
        
        bSizer10.Add( bSizer7, 3, wx.ALIGN_CENTER, 5 )
        
        bSizer4.Add( bSizer10, 0, wx.EXPAND, 5 )
        
        self.m_panel3 = wx.Panel( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer92 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_checkBox1 = wx.CheckBox( self.m_panel3, wx.ID_ANY, u"Copy Results", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox1.SetValue(True) 
        bSizer92.Add( self.m_checkBox1, 0, wx.ALL, 5 )
        
        
        #bSizer92.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
        
        bSizer13 = wx.BoxSizer( wx.VERTICAL )
        
        bSizer92.Add( bSizer13, 1, wx.EXPAND, 5 )
        
        self.m_button4 = wx.Button( self.m_panel3, wx.ID_ANY, u"&Pause", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer92.Add( self.m_button4, 0, wx.ALL, 5 )
        
        self.m_button5 = wx.Button( self.m_panel3, wx.ID_ANY, u"&Resume", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button5.Enable( False )
        
        bSizer92.Add( self.m_button5, 0, wx.ALL, 5 )
        
        
        
        bSizer14 = wx.BoxSizer( wx.VERTICAL )
        
        bSizer92.Add( bSizer14, 1, wx.EXPAND, 5 )
        
        self.m_panel3.SetSizer( bSizer92 )
        self.m_panel3.Layout()
        bSizer92.Fit( self.m_panel3 )
        bSizer4.Add( self.m_panel3, 1, wx.ALL|wx.EXPAND, 5 )
        
        self.m_panel2.SetSizer( bSizer4 )
        self.m_panel2.Layout()
        bSizer4.Fit( self.m_panel2 )
        bSizer8.Add( self.m_panel2, 0, 0, 0 )
        
        self.SetSizer( bSizer8 )
        self.Layout()
        
        # Connect Events
        self.m_button2.Bind( wx.EVT_BUTTON, self.OnExit )
        self.m_button3.Bind( wx.EVT_BUTTON, self.OnStop )
        self.m_button51.Bind( wx.EVT_BUTTON, self.OnNext )
        self.m_button6.Bind( wx.EVT_BUTTON, self.OnLast )
        self.m_button4.Bind( wx.EVT_BUTTON, self.OnPause )
        self.m_button5.Bind( wx.EVT_BUTTON, self.OnResume )
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        self.m_checkBox1.Bind( wx.EVT_CHECKBOX, self.boxChanged )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def OnCloseFrame(self, event):
        event.Skip()
        
    def OnExit( self, event ):
        event.Skip()
    
    def OnStop( self, event ):
        event.Skip()
    
    def OnNext( self, event ):
        event.Skip()
    
    def OnLast( self, event ):
        event.Skip()
    
    def OnPause( self, event ):
        event.Skip()
    
    def OnResume( self, event ):
        event.Skip()
        
    def boxChanged( self, event ):
        event.Skip()
    

