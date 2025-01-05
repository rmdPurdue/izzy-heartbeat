# izzy-heartbeat
The `izzy-heartbeat` package provides the classes that allow for heartbeat communication in the IZZY 
(Intelligent Scenery Simulation Project) as well as enumerations for port numbers and types of heartbeat messages.

## Installation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install `izzy-hearbeat`.
```bash
pip install izzy-heartbeat
```

## Background
"IZZY," or the Intelligent Scenery Simulation Platform, is an ongoing research project in applied robotics and 
control systems for moving scenery in live entertainment. Computerized control of scenery is not new; technologies 
for controlling both simple and complex movement of scenery in multiple axes have been around for decades. Many 
traditional approaches borrow heavily from industrial automation systems, employing programmable logic controllers 
(sometimes with more-user-friendly PC-style front-end interfaces), roller switches, high-powered motors, and cable 
winches. However, because of the very real safety concerns related to hauling scenic units weighing as much as a 
couple of tons across the stage at relatively high velocities, typical automation systems rely heavily on 
highly-choreographed movements and attentive operators to ensure safety. Additionally, traditional approaches often 
require the construction of expensive sub-floors and decking systems to provide pathways for winched cables and 
tracks for scenic units to follow.

## IZZY and Mother
The IZZY (Intelligent Scenery Simulation Platform) project software is built around two software objects: a client
and a server. An implementation of IZZY is a ``client``; the offstage control and programming interface ``server`` has
been affectionately dubbed "Mother" (a not-so-subtle nod to *Alien*). A ``client`` stores information about an IZZY
device, including physical dimensions, network information installed sensor packages, and position and movement
information. A ``server`` stores network information and a collection of ``client`` instances--one instance for each
physical IZZY device on the network.

## Communication
### Heartbeat
To address emergency stop requirements and loss of communication safety concerns, the IZZY project implements a 
heartbeat protocol between IZZY client devices and Mother servers. When the heartbeat signal is lost, IZZY clients 
shutdown. Hitting an e-stop button wherever the Mother application is running cuts off the heartbeat signal, 
triggering a shutdown and system reset.

Upon startup, Mother servers begin sending out Heartbeat ``hello`` message packets as broadcast UDP messages. Any 
powered up IZZY clients on the same network will respond to ``hello`` messages by sending a ``here`` message packet 
which contains a data payload with status information about the client. The status information can change depending 
on the operating mode the client is in; at a minimum, an IZZY client Heartbeat response will include its 
user-friendly name, its status/operating mode, its position in x, y, and z directions, its heading, and its current 
speed.

### Heartbeat Messages and Packets
Heartbeat messages are programmatically created and stored in custom ``HeartbeatMessage`` objects. Heartbeat *packets*,
the raw UDP data that is sent and received, comprise up to 255 bytes of information (46 required bytes and up to 209 
status/data payload bytes). Packets begin with a one-byte preamble (0x10) and are followed immediately by an 11-byte 
IZZY project identifier ("izzymessage," or 0x69 0x7A 0x7A 0x79 0x6D 0x65 0x73 0x73 0x61 0x67 0x65). The next byte 
contains the total length of the packet. The next 16 bytes contain the 64-bit UUID of the sending device followed by 
the 64-bit UUID of the receiving device. This is followed by a one-byte Message Type identifier, then the data 
payload, which can be up to 209 bytes long.

| Preamble | Message ID                                             | Message Length | Sender UUID | Receiver UUID | Message Type | Payload     |
|----------|--------------------------------------------------------|----------------|-------------|---------------|--------------|-------------|
| 0x10     | 0x69 0x7A 0x7A 0x79 0x6D 0x65 0x73 0x73 0x61 0x67 0x65 | 1 byte         | 8 bytes     | 8 bytes       | 1 byte       | 0-209 bytes |

`HeartbeatMessages` (instances of the `HeartbeatMessage` class) are different from raw Heartbeat *packets* in that
each instance includes attributes for storing each chunk of a packet separately. This allows for easy 
programmatic manipulation of the message data when necessary.

>[!NOTE]
>Improperly structured Heartbeat packets will not be interpreted correctly.

### Threading
Heartbeat sending and receiving happens on separate threads than the rest of the application, whether on a ``client``
or a ``server``. This allows for non-blocking processing and for (relatively) timely delivery and response of
heartbeat packets. The package provides three classes to facilitate this: ``HeartbeatServerThread``,
``HeartbeatListenerThread``, and ``HeartbeatResponderThread``.