import struct
import threading
import time
from datetime import datetime
from uuid import UUID
from izzy_heartbeat.message_type import MessageType
from izzy_heartbeat.ports import Ports
from izzy_devices import IZZYStatus
from izzy_devices import MotherStatus
from logger import setup_logger


logger = setup_logger(__name__, 'heartbeat-log')


class HeartbeatMessage:
    """
    Generates, holds, and deconstructs the bytes in a Heartbeat packet.

    preamble
        The first byte of a heartbeat packet. Must be 0x10.

    msg_id
        11-byte sequence identifying the packet as an IZZY heartbeat packet ('izzymessage'
        or 0x69, 0x7A, 0x7A, 0x79, 0x6D, 0x65, 0x73, 0x73, 0x61, 0x67, 0x65).

    msg_length
        A byte representing the total number of bytes in the packet.

    sender_id
        The 64-bit UUID of the sending device.

    receiver_id
        The 64-bit UUID of the receiving device.

    message_type
        A byte representing the Heartbeat MessageType.

    data
        The data payload.
    """

    def __init__(self, message_type=None):
        """
        HeartbeatMessage constructor.

        Parameters
        ----------
        message_type
            Takes values of enumerated pre-defined MessageTypes. Defaults to none. In most cases, Mother will
            generate messages of type HELLO (0x01).
        """
        self.preamble = 0x10
        self.msg_id = [0x69, 0x7A, 0x7A, 0x79, 0x6D, 0x65, 0x73,
                       0x73, 0x61, 0x67, 0x65]  # 'izzymessage'
        self.msg_length = 46
        self.sender_id = None
        self.receiver_id = None
        self.message_type = message_type
        self.data = None

    def set_data(self, data):
        """
        Fills the data payload of the message, and updates the total length of the message by adding the length of
        the data payload to the base length of the message (46 bytes).

        Parameters
        ----------
        data
            A bytearray of data.
        """
        self.data = data
        if self.data is not None:
            self.msg_length = 46 + len(self.data)

    def get_message(self):
        """
        Returns
        -------
        bytearray
            a bytearray containing the sequence of bytes in the packet.

        """
        message = bytearray()
        message.append(self.preamble)

        if self.msg_id is not None:
            for byte in self.msg_id:
                message.append(byte)
        else:
            for i in range(0, 11):
                message.append(0x00)

        message.append(self.msg_length)

        if self.sender_id is not None:
            for byte in self.sender_id.bytes:
                message.append(byte)
        else:
            for i in range(0, 16):
                message.append(0x00)

        if self.receiver_id is not None:
            for byte in self.receiver_id.bytes:
                message.append(byte)
        else:
            for i in range(0, 16):
                message.append(0x00)

        message.append(self.message_type)

        if self.data is not None:
            for byte in self.data:
                message.append(byte)

        return message

    def process_packet(self, raw_data):
        """
        Takes a packet of received data (as a bytearray) and unpacks it, filling the attributes of the instance of
        HeartbeatMessage with the appropriate bytes provided the length of the packet matches the length byte sent
        in the packet.

        Parameters
        ----------
        raw_data
            a bytearray containing a raw packet

        Returns
        -------
        boolean
            True if the packet is the correct length and the bytes in the packet have populated the HeartbeatMessage
            instance; otherwise False.
        """

        data = bytes(raw_data)
        self.preamble = data[0]
        self.msg_id = bytes(data[1:12])
        if len(raw_data) == data[12]:
            self.msg_length = data[12]
            self.sender_id = UUID(bytes=data[13:29])
            self.receiver_id = UUID(bytes=data[29:45])
            self.message_type = data[45]
            if len(data) > 46:
                self.data = data[46:len(data)]
            else:
                self.data = None
            return True
        else:
            return False


class HeartbeatServerThread(threading.Thread):
    """Creates a separate worker thread for sending ``HeartbeatMessage`` packets.

    send_socket (socket)
        UDP socket for sending Heartbeat packets.

    message (HeartbeatMessage)
        The bytes of a ``HeartbeatMessage`` to send (as a bytearray).

    interval (int)
        The delay between packet pulses (in seconds).

    _running (boolean)
        A boolean to control stopping the thread, if necessary.

    """

    def __init__(self, send_socket, message, interval=1):
        """
        Default constructor. Extends ``threading.Thread``.

        Parameters
        ----------
        send_socket (socket)
            a socket for sending packets

        message (HeartBeatMessage)
            a message to send

        interval (int)
            time interval between sending packets, in seconds
        """
        super().__init__(daemon=True)
        self.send_socket = send_socket
        self.message = message
        self.interval = interval
        self._running = True

    def run(self):
        """
        Starts the ``HeartbeatThread``, which will run as long as the `_running` flag is True. Sends the message and
        after waiting the specified interval, in a loop.
        """
        while self._running:
            self.send_socket.sendto(self.message.get_message(),
                                    ('255.255.255.255', Ports.UDP_TO_CLIENT_PORT.value))
            logger.info("(%s) (server) - Heartbeat pulse sent.", format(__name__))
            time.sleep(self.interval)

    def stop(self):
        """
        Sets the `_running` flag to False.
        """
        self._running = False


class HeartbeatListenerThread(threading.Thread):
    """
    Creates a separate worker thread for receiving ``Heartbeat`` message packets. Packets are stored as raw bytes.

    rcv_socket (socket)
        UDP socket for receiving Heartbeat response packets.

    _running (boolean)
        A boolean to control stopping the thread, if necessary.

    hb_messages (Queue)
        A ``Queue`` for placing received messages.

    message (HeartbeatMessage)
        A ``HeartbeatMessage`` instance for packaging received packets as a message.
    """
    def __init__(self, rcv_socket, messages, signal):
        """
        Default constructor. Extends ``threading.Thread``.

        Parameters
        ----------
        rcv_socket (socket)
            UDP socket for receiving Heartbeat response packets.

        messages (Queue)
            A ``Queue`` for placing received messages.

        signal (Signal)
            A ``signalslot`` ``Signal`` for triggering other actions when a message is received.
        """
        super().__init__(daemon=True)
        self.rcv_socket = rcv_socket
        self._running = True
        self.hb_messages = messages
        self.message = HeartbeatMessage()
        self.signal = signal

    def run(self):
        """
        Starts the ``HeartbeatListenerThread``, which will run as long as the `_running` flag is True. Receives UDP
        packets, extracts the IP address and port of the sender, and creates a new ``HeartbeatMessage`` populated
        from the packet. Then it places a tuple containing the length of the packet, the address of the sender (as a
        tuple with the IP address and the port number), and the packet itself on the message queue.
        """
        while self._running:
            data, address = self.rcv_socket.recvfrom(1024)
            logger.info(f"(%s) (listener)- Heartbeat received", format(__name__))
            self.message.process_packet(data)
            # logger.debug(f"(%s) (listener) - Data length: {len(data)}; from {address}: {self.message}.",
                         # format(__name__))
            self.hb_messages.put((len(data), self.message,
                                 address))
            # logger.debug(f"(%s) (listener) - Queue length: {self.hb_messages.qsize()}.", format(__name__))
            if self.signal is not None:
                self.signal.emit()

    def stop(self):
        """
        Sets the `_running` flag to False.
        """
        self._running = False


class HeartbeatResponderThread(threading.Thread):
    def __init__(self, send_socket, hb_messages, izzy, mother):
        super().__init__(daemon=True)
        self.send_socket = send_socket
        self._running = True
        self.hb_messages = hb_messages
        self.received_message = HeartbeatMessage()
        self.reply_message = HeartbeatMessage()
        self.mother = mother
        self.izzy = izzy

    def run(self):
        while self._running:
            data = bytearray()
            length, self.received_message, address = self.hb_messages.get()
            # logger.debug(f"(%s) (responder) - Preamble: {self.received_message.preamble}.", format(__name__))
            if self.received_message.preamble == int(0x10):
                if list(self.received_message.msg_id) == [0x69, 0x7A, 0x7A, 0x79, 0x6D, 0x65,
                                                          0x73, 0x73, 0x61, 0x67, 0x65]:
                    if self.received_message.message_type == MessageType.HELLO.value:
                        # logger.debug(f"(%s) (responder) - Message is a heartbeat pulse.", format(__name__))
                        if (self.mother.uuid is None or self.mother.uuid !=
                                self.received_message.sender_id):
                            self.mother.uuid = self.received_message.sender_id
                            self.mother.ip_address = address[0]
                            self.mother.status = MotherStatus.CONNECTED.value
                            # logger.debug("(%s) (responder) - First pulse received. Initializing Mother.",
                            # format(__name__))
                        self.reply_message.sender_id = self.izzy.uuid
                        self.reply_message.receiver_id = self.mother.uuid
                        self.izzy.last_contact = datetime.now()
                        data.extend(self.izzy.build_base_response())
                        # logger.debug(f"(%s) (responder) - base payload: {data}", format(__name__))
                        self.reply_message.message_type = MessageType.HERE.value
                        match self.izzy.status:
                            case IZZYStatus.AVAILABLE.value:
                                pass
                            case IZZYStatus.MOVING.value:
                                pass
                            case IZZYStatus.FOLLOWING.value:
                                data = self.izzy.build_following_response()
                            case IZZYStatus.ESTOP.value:
                                pass
                            case _:
                                pass
                        self.reply_message.set_data(data)
                        # logger.debug(f"(%s) (responder) - follower payload: {data}", format(__name__))
                        # logger.debug(f"(%s) (responder) - message length: {self.reply_message.msg_length}",
                        #             format(__name__))
                        time.sleep(0.1)
                        self.send_socket.sendto(self.reply_message.get_message(),
                                                (self.mother.ip_address, Ports.UDP_FROM_CLIENT_PORT.value))
                        # logger.debug(f"(%s) (responder) - Reply sent: {self.reply_message.get_message()}",
                        #             format(__name__))
                    else:
                        pass
                else:
                    pass
            else:
                pass
