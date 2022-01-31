"""CD Chat client program"""
import fcntl
import logging
import socket
import selectors
import sys
import os

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel = None
        self.channel_dict = {}

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('localhost', 12345))
        self.s.setblocking(False)
        print("Welcome to CD Chat, {}!".format(self.name))


    def loop(self):
        """Loop indefinetely."""
        try:
            # set sys.stdin non-blocking
            orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
            fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK) 
            self.sel.register(sys.stdin, selectors.EVENT_READ, self.read_input) # read_input é a função de callback
            self.sel.register(self.s, selectors.EVENT_READ, self.print_data) # print_data é a função de callback

            #try:
            msg_proto = CDProto.register(self.name)
            CDProto.send_msg(self.s, msg_proto)

            while True:
                sys.stdout.write(">>> ")
                sys.stdout.flush() 

                for k, mask in self.sel.select():
                    callback = k.data
                    callback(k.fileobj, mask)
                    
        except KeyboardInterrupt:
            print("")
            sys.exit(0)
        
        except socket.error:
            print("Something wrong occurred...")
            sys.exit(0)


    def read_input(self, conn, mask):  # criar funçao read_input, ler stdin e enviar
        line = sys.stdin.readline()
        if str(line.strip()) == "exit": # terminar programa cliente
            print("Client {} left the chat.".format(self.name))
            self.s.close()
            self.sel.unregister(self.s)
            sys.exit(0)
        elif str(line.strip()).startswith("/join"):
            self.entry_channel(line)
        else:
            msg_proto = CDProto.message(line, self.channel)
            CDProto.send_msg(self.s, msg_proto)

    def print_data(self, conn, mask): # criar funçao print_data, receber resposta e dar print
            data = CDProto.recv_msg(self.s)
            logging.debug("Data: %s", data)
            if data != "":
                print(data.message)
                    
    def entry_channel(self, line):
        line_splitted = line.strip().split(" ")
        if len(line_splitted)==1: # se apenas for escrito /join
            print("Should write a channel to join!")
        else:
            try:
                self.channel = line_splitted[-1]
                self.channel_dict[self.name] = self.channel
                msg_proto = CDProto.join(self.channel)
                CDProto.send_msg(self.s, msg_proto)
            except:
                raise(CDProtoBadFormat)



