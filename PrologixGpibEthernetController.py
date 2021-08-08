import os
import sys
import time
import socket

#print('The number of args is: {}'.format(len(sys.argv)))
#print('args values are: {}'.format(sys.argv))

def hello_world():
    print('Hello world!')
    
#hello_world()

class PrologixControl:
    def __init__(self, ip, port, gpib):
        self.BUFSIZ = 1024
        self.HOST = ip
        self.PORT = int(port)
        self.ADDR = (self.HOST, self.PORT)
        self.timeout = 1
        self.gpibAdd = gpib
        #print(self.ADDR, self.gpibAdd, self.BUFSIZ)
        try:
            self.prolSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket
            self.prolSock.settimeout(self.timeout)
            self.prolSock.connect(self.ADDR)                    # connect a socket    
        except socket.error as e:
            return "Python Error conecting: " + str(e)
        #self.set_defaults()
        
    def sockClose(self):
        #print('closing socket')
        self.prolSock.close()

    #def __del__(self):
    #    self.close()
        
    def set_defaults(self):
        """ Sets up the default behavior of the Prologix-GPIB
        adapter
        """
        self.write("++auto 0")  # Turn off auto read-after-write
        self.write("++eoi 1")  # Append end-of-line to commands
        self.write("++eos 2")  # Append line-feed to commands
        self.write("++read_tmo_ms 500")  # Append line-feed to commands

    def ask(self, command):
        """ Ask the Prologix controller, include a forced delay for some instruments.

        :param command: SCPI command string to be sent to instrument
        """

        self.write(command)
        return self.read()

    def write(self, command):
        """ Writes the command to the GPIB address stored in the
        :attr:`.address`

        :param command: SCPI command string to be sent to the instrument
        """
        if self.gpibAdd is not None:
            address_command = "++addr %d\n" % int(self.gpibAdd)
            self.connection_write(address_command)
        self.connection_write(command)

    def read(self):
        """ Reads the response of the instrument until timeout

        :returns: String ASCII response of the instrument
        """
        return self.connection_read("++read")
    
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
            return "Python Error sending data: " + str(e)
        #time.sleep((0.1, 2)["*RST" in cmd])
        #time.sleep((0.1, 3)["MMEM:LOAD" in cmd])
        
    def read_poll(self, repeat):
        start_time = time.time()
        mesg = ""
        for _ in range(repeat):
            try:
                sendData = "++read\n"
                self.prolSock.send(sendData.encode())
                mesg = self.prolSock.recv(self.BUFSIZ)
                break
            except socket.timeout:
                time.sleep(1)
            except socket.error as e:
                return "Python Error sending data: " + str(e)
        #print("read poll operation took {:.0f} seconds".format(time.time() - start_time))
        return mesg
     
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
            if "*OPC?" in cmd:
                sendData = cmd.replace("?", "")
                self.write(sendData)
                for _ in range(30):
                    ask_dmm = dmm.ask("*ESR?").strip()
                    if '+1' == ask_dmm:
                        return ask_dmm
                    time.sleep(1)
            else:
                sendData = cmd + "\n"
                time.sleep(0.1)
                self.prolSock.send(sendData.encode())                        # Send the command with end charaters
                mesg = self.prolSock.recv(self.BUFSIZ)              # Read the response
                #time.sleep(0.5)
                #self.prolSock.close()                          # Close the socket
        except socket.timeout:
            mesg = self.read_poll(30)
        except socket.error as e:
            return "Python Error sending data: " + str(e)
        #print('recieve: {}'.format(mesg.strip()))
        if mesg != "":
            mesg = mesg.decode()
        return mesg

prol = PrologixControl(sys.argv[1], sys.argv[2], sys.argv[3])
if "?" in sys.argv[4]:
    #print("Sir, I have a question: "+sys.argv[4])
    try:
        mesg = '{}'.format(prol.ask(sys.argv[4]).strip())
        if 'Python Error' not in mesg:
            print(mesg)
    except:
        try:
            print('{}'.format(prol.ask(sys.argv[4]).strip()))
        except:
            print('second error')
else:
    prol.write(sys.argv[4])
prol.sockClose()