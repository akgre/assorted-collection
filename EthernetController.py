import os
import sys
import time
import socket

#print('The number of args is: {}'.format(len(sys.argv)))
#print('args values are: {}'.format(sys.argv))

def hello_world():
    print('Hello world!')
    
#hello_world()

class EthernetControl:
    def __init__(self, ip, port, gpib):
        self.BUFSIZ = 4096
        self.HOST = ip
        self.PORT = int(port)
        self.ADDR = (self.HOST, self.PORT)
        self.timeout = 60
        self.gpibAdd = gpib
        #print(self.ADDR, self.gpibAdd, self.BUFSIZ)
        try:
            self.prolSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
            self.prolSock.settimeout(self.timeout)
            self.prolSock.connect(self.ADDR)                    # connect a socket    
        except socket.error as e:
            print("Error conecting: " + str(e))
        #self.set_defaults()
        
    def sockClose(self):
        #print('closing socket')
        self.prolSock.close()

    #def __del__(self):
    #    self.close()

    def ask(self, command):
        """ Ask the Prologix controller, include a forced delay for some instruments.

        :param command: SCPI command string to be sent to instrument
        """

        #self.write()
        return self.read(command)

    def write(self, command):
        """ Writes the command to the GPIB address stored in the
        :attr:`.address`

        :param command: SCPI command string to be sent to the instrument
        """
        self.connection_write(command)

    def read(self, command):
        """ Reads the response of the instrument until timeout

        :returns: String ASCII response of the instrument
        """
        return self.connection_read(command)
    
    def connection_write(self, cmd):
        #try:
        #    self.prolSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
        #    self.prolSock.connect(self.ADDR)                    # connect a socket  
        #except socket.error as e:
        #    print("Error conecting: " + str(e))
        try:
            #print(('send '+cmd).strip())
            sendData = cmd + "\n"
            self.prolSock.send(sendData.encode())                        # Send the command with end charater
            time.sleep(0.1)
            #self.prolSock.close()                          # Close the socket
        except socket.error as e:
            print("Error sending data: " + str(e))
        #time.sleep((0.1, 2)["*RST" in cmd])
        #time.sleep((0.1, 3)["MMEM:LOAD" in cmd])
        
    def read_poll(self, repeat):
        start_time = time.time()
        mesg = "no returned data"
        for _ in range(repeat):
            try:
                #self.prolSock.send(sendData.encode())
                mesg = self.prolSock.recv(self.BUFSIZ)
                break
            except socket.timeout:
                pass
            except socket.error as e:
                print("Error sending data: " + str(e))
        #print("read poll operation took {:.0f} seconds".format(time.time() - start_time))
        return mesg.strip()
     
    def connection_read(self, cmd):
        #mesg = ""
        #try:
        #    self.prolSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
        #    self.prolSock.connect(self.ADDR)                    # connect a socket    
        #except socket.error as e:
        #    print("Error conecting: " + str(e))
        mesg = ""
        try:
            #print(('send '+cmd).strip())
            sendData = cmd + "\n"
            time.sleep(0.1)
            self.prolSock.send(sendData.encode())                        # Send the command with end charaters
            soc_buffer = self.prolSock.recv(self.BUFSIZ)
            buffering = True          
            while buffering:
                if "\n" in soc_buffer.decode():
                    buffering = False
                else:
                    more = self.prolSock.recv(self.BUFSIZ)
                    if "\n" in more.decode():
                        soc_buffer += more
                        buffering = False
                    else:
                        soc_buffer += more
            #if buffer:
            #    yield buffer
            mesg = soc_buffer
            #time.sleep(0.5)
            #self.prolSock.close()                          # Close the socket
        except socket.timeout:
            #mesg = self.read_poll(20)
            pass
        except socket.error as e:
            print("Error sending data: " + str(e))
        except:
            print("Error sending data: ")
        if mesg != "":
            mesg = mesg.decode()
        return mesg #.strip()
'''
eCon = EthernetControl(sys.argv[1], sys.argv[2], sys.argv[3])
if "?" in sys.argv[4]:
    #print("Sir, I have a question: "+sys.argv[4])
    print('{}'.format(eCon.ask(sys.argv[4]).strip()))
else:
    eCon.write(sys.argv[4])
eCon.sockClose()
'''