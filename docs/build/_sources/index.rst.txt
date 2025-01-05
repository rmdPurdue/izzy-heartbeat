izzy-heartbeat documentation
============================

.. include:: ../../README.md
   :start-after: ### Heartbeat
   :end-before: ### Heartbeat Messages


.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. contents::
   :local:

Heartbeat Messages and Packets
******************************
.. include:: ../../README.md
   :start-after: ### Heartbeat Messages and Packets
   :end-before: Preamble

.. table:: Heartbeat Message Packet Structure
   :widths: auto

   ======== ========== ============== =========== ============= ============ ===========
   Preamble Message ID Message Length Sender UUID Receiver UUID Message Type Payload
   ======== ========== ============== =========== ============= ============ ===========
   0x10     0x69 0x7A  1 byte         8 bytes     8 bytes       1 byte       0-209 bytes
            0x7A 0x79
            0x6D 0x65
            0x73 0x73
            0x61 0x67
            0x65
   ======== ========== ============== =========== ============= ============ ===========

`HeartbeatMessages` (instances of the `HeartbeatMessage` class) are different than raw Heartbeat *packets* in that
each instance includes attributes for storing each chunk of a packet separately. This allows for easy
programmatic manipulation of the message data when necessary.

.. note::
   Improperly structured Heartbeat packets will not be interpreted correctly.

Threading
*********
Heartbeat sending and receiving happens on separate threads than the rest of the application, whether on a ``client``
or a ``server``. This allows for non-blocking processing and for (relatively) timely delivery and response of
heartbeat packets. The package provides three classes to facilitate this: ``HeartbeatServerThread``,
``HeartbeatListenerThread``, and ``HeartbeatResponderThread``.

HeartbeatMessage
****************
.. autoclass:: heartbeat.HeartbeatMessage
   :members:

HeartbeatServerThread
*********************
.. autoclass:: heartbeat.HeartbeatServerThread
   :members:

HeartbeatListenerThread
***********************
.. autoclass:: heartbeat.HeartbeatListenerThread
   :members:

HeartbeatResponderThread
************************
.. autoclass:: heartbeat.HeartbeatResponderThread
   :members:

Message Types
*************
.. automodule:: message_type
   :members:

Port Numbers
************
.. automodule:: ports
   :members:
