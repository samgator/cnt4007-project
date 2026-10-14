"""Wire protocol specification and serialization/deserialization routines.

Implements:
- 32-byte Handshake header and peer ID verification.
- Standard length-prefixed messages (types 0-7).
- Bitfield encoding/decoding and bit-level manipulation.
"""

import math
import struct
from typing import Set, Tuple

# Handshake specifications
HANDSHAKE_HEADER = b"P2PFILESHARINGPROJ"
HANDSHAKE_HEADER_LEN = 18
HANDSHAKE_ZEROS_LEN = 10
HANDSHAKE_TOTAL_LEN = 32

# Message types
MSG_CHOKE = 0
MSG_UNCHOKE = 1
MSG_INTERESTED = 2
MSG_NOT_INTERESTED = 3
MSG_HAVE = 4
MSG_BITFIELD = 5
MSG_REQUEST = 6
MSG_PIECE = 7

MESSAGE_NAMES = {
    MSG_CHOKE: "choke",
    MSG_UNCHOKE: "unchoke",
    MSG_INTERESTED: "interested",
    MSG_NOT_INTERESTED: "not interested",
    MSG_HAVE: "have",
    MSG_BITFIELD: "bitfield",
    MSG_REQUEST: "request",
    MSG_PIECE: "piece",
}

def encode_message(msg_type: int, payload: bytes = b"") -> bytes:
    """Encodes a standard protocol message.
    
    Format: [4-byte length][1-byte type][payload]
    Length counts only 1 byte (type) + len(payload).
    """
    length = 1 + len(payload)
    return struct.pack(">IB", length, msg_type) + payload
