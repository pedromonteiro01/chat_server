"""CD Chat server program."""
import logging
import socket
import selectors
import sys

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""
    # criar construtor

    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', 12345))
        self.s.listen(10)
        self.sel.register(self.s, selectors.EVENT_READ, self.accept)
        self.clients_num = 1
        self.conns_channels = {}  # colocar as conns como keys e os channels como values
        print("Server started!")

    def accept(self, sock, mask):
        (conn, addr) = sock.accept()
        print("Connection from {} and port {} has been established!".format(addr[0], addr[1]))
        print("{} client(s) active.".format(self.clients_num))
        self.clients_num += 1
        conn.setblocking(False)  # non-blocking
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):

        try:
            data = CDProto.recv_msg(conn)

        except CDProtoBadFormat:
            print("Error receiving data...")

        if data:
            print('echoing', repr(data), 'to', conn)
            logging.debug("echoing %s", data)
            if data.command == "register":
                self.conns_channels[conn] = list() # adicionar ao dicionario a conexao com uma lista vazia de channels
            elif data.command == "join": # se o comando for join deve acrescentar a lista o channel
                self.conns_channels[conn].append(data.channel)
                print(self.conns_channels)
            elif data.command == "message":  # se for do tipo message deve ver o channel e enviar
                if len(self.conns_channels[conn]) == 0:  # nao ha channel!
                    for conn_key in self.conns_channels.keys():
                        CDProto.send_msg(conn_key, data)
                else:
                    channel = data.channel # channel atual
                    for conn_key, channel_value in self.conns_channels.items():
                        for c in channel_value: # para cada channel dentro da lista de todos os channels
                            if c == channel:
                                CDProto.send_msg(conn_key, data)

        else:
            print('closing', conn)
            logging.debug("Closing: %s",conn)
            conn.close()
            self.sel.unregister(conn)
            if conn in self.conns_channels:
                del self.conns_channels[conn] # remover a conexao para quando um cliente sair
            if len(self.conns_channels) == 0:
                print("All clients disconnected. Waiting...")
                self.clients_num = 1

    def loop(self):
        """Loop indefinetely."""
        try:
            while True:
                for key, mask in self.sel.select():
                    callback = key.data
                    callback(key.fileobj, mask)

        except KeyboardInterrupt:
            print("")
            sys.exit(0)

        except socket.error:
            print("Something wrong occurred...")
            sys.exit(0)
