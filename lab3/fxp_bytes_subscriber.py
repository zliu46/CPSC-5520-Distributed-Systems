"""
CPSC 5520, Seattle University

This module provides utility functions for handling Forex data in a UDP-based 
currency arbitrage detection system. It includes functions to decode incoming 
quote messages and to construct subscription request messages.

:Authors: Zhou Liu
:Version: f24-02
"""
import struct
import socket

def read_quote(data):
    """
    Decodes a quote from a byte stream.

    Parameters:
        data (bytes): 32-byte message containing currency codes, exchange rate, and ts.

    Returns:
        tuple: (currency1 (str), currency2 (str), rate (float), ts (int))
    """
    # Decode currency codes (3 bytes each) from ASCII
    currency1 = data[0:3].decode('ascii')
    currency2 = data[3:6].decode('ascii')
    
    # Extract exchange rate (4 bytes, little-endian float)
    rate = struct.unpack('<f', data[6:10])[0]
    
    # Extract ts (8 bytes, big-endian unsigned integer)
    ts = struct.unpack('>Q', data[10:18])[0]
    
    return currency1, currency2, rate, ts

def sub_request(ip, port):
    """
    Constructs a subscription request message to send to the publisher.

    Parameters:
        ip (str): IP address of the subscriber.
        port (int): Port number of the subscriber.

    Returns:
        bytes: 6-byte message containing the IP and port in network byte order.
    """
    # Convert IP to 4-byte format (network byte order)
    ip_bytes = socket.inet_aton(ip)
    
    # Convert port to 2-byte big-endian format
    port_bytes = struct.pack('>H', port)
    
    return ip_bytes + port_bytes
