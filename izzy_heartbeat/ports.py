"""
Ports.py
=================================
Enumerates UDP port numbers for Heartbeat and OSC communication.
"""

from enum import Enum


class Ports(Enum):
    """
    An enumeration class for network ports used by the project.
    Extends class Enum from enum.
    """

    UDP_TO_CLIENT_PORT = 9001
    UDP_FROM_CLIENT_PORT = 9000
    OSC_TO_CLIENT_PORT = 8001
    OSC_FROM_CLIENT_PORT = 8000
