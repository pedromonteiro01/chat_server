"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""

    def __init__(self, command):
        self.command = command

    def __repr__(self):
        return self.__str__()


class RegisterMessage(Message):
    """Message to register username in the server."""

    def __init__(self, command, name):
        super(RegisterMessage, self).__init__(command)
        self.name = name

    # definir toString para pytest
    def __str__(self):
        return f'{{"command": "{self.command}", "user": "{self.name}"}}'


class JoinMessage(Message):
    """Message to join a chat channel."""

    def __init__(self, command, channel):
        super(JoinMessage, self).__init__(command)
        self.channel = channel

    # definir toString para pytest
    def __str__(self):
        return f'{{"command": "{self.command}", "channel": "{self.channel}"}}'


class TextMessage(Message):
    """Message to chat with other clients."""

    def __init__(self, command, message, ts, channel=None):
        super(TextMessage, self).__init__(command)
        self.message = message
        self.ts = ts
        self.channel = channel

    def __str__(self):  # definir toString para pytest
        if self.channel == None:  # se o channel for None passar json sem channel
            return f'{{"command": "{self.command}", "message": "{self.message}", "ts": {self.ts}}}'
        else:
            return f'{{"command": "{self.command}", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        command = "register"
        # criar um objeto do tipo RegisterMessage
        user = RegisterMessage(command, username)
        return user

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        command = "join"
        # criar um objeto do tipo JoinMessage
        channel = JoinMessage(command, channel)
        return channel

    @classmethod
    # valor default do channel é None
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        command = "message"
        # datetime.now() -> 2021-04-03 21:04:06.464650
        ts = int(datetime.now().timestamp())
        # criar um objeto do tipo TextMessage
        msg = TextMessage(command, message, ts, channel)
        return msg

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        msg_json = check_msg_type(cls, msg)
        msg_length = len(msg_json).to_bytes(2, "big")
        connection.send(msg_length + msg_json)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        json_size = connection.recv(2)
        json_size = int.from_bytes(json_size, "big")
        json_recv = connection.recv(json_size).decode("utf-8")

        if json_size != 0:
            try:
                data = json.loads(json_recv)

                if data["command"] == "register":
                    return RegisterMessage("register", data["user"])

                elif data["command"] == "join":
                    return JoinMessage("join", data["channel"])

                elif data["command"] == "message":
                    if "channel" in data:
                        return TextMessage("message", data["message"], data["ts"], data["channel"])
                    else:
                        return TextMessage("message", data["message"], data["ts"])

            except:
                raise CDProtoBadFormat(json_recv)


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes = None):
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")


def check_msg_type(self, msg):
    if type(msg) == RegisterMessage:
        msg = json.dumps({"command": "register", "user": msg.name})
    elif type(msg) == JoinMessage:
        msg = json.dumps({"command": "join", "channel": msg.channel})
    elif type(msg) == TextMessage:
        if msg.channel == None:  # se o channel for None nao se deve enviar no json
            msg = json.dumps(
                {"command": "message", "message": msg.message.strip(), "ts": msg.ts})
        else:
            msg = json.dumps({"command": "message", "message": msg.message.strip(
            ), "channel": msg.channel, "ts": msg.ts})
    return msg.encode("utf-8")
