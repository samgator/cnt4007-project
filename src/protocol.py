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

def make_handshake(peer_id: int) -> bytes:
    """Constructs the 32-byte handshake message."""
    return HANDSHAKE_HEADER + (b"\x00" * HANDSHAKE_ZEROS_LEN) + struct.pack(">I", peer_id)


def parse_handshake(data: bytes) -> Tuple[bool, int]:
    """Parses and validates a 32-byte handshake message.
    
    Returns (is_valid_header, peer_id).
    """
    if len(data) != HANDSHAKE_TOTAL_LEN:
        return False, 0
    header = data[:HANDSHAKE_HEADER_LEN]
    if header != HANDSHAKE_HEADER:
        return False, 0
    peer_id = struct.unpack(">I", data[28:32])[0]
    return True, peer_id
    
    
def encode_message(msg_type: int, payload: bytes = b"") -> bytes:
    """Encodes a standard protocol message.
    
    Format: [4-byte length][1-byte type][payload]
    Length counts only 1 byte (type) + len(payload).
    """
    length = 1 + len(payload)
    return struct.pack(">IB", length, msg_type) + payload
    

def make_choke() -> bytes:
    return encode_message(MSG_CHOKE)


def make_unchoke() -> bytes:
    return encode_message(MSG_UNCHOKE)


def make_interested() -> bytes:
    return encode_message(MSG_INTERESTED)


def make_not_interested() -> bytes:
    return encode_message(MSG_NOT_INTERESTED)


def make_have(piece_index: int) -> bytes:
    return encode_message(MSG_HAVE, struct.pack(">I", piece_index))


def make_bitfield_msg(bitfield_bytes: bytes) -> bytes:
    return encode_message(MSG_BITFIELD, bitfield_bytes)


def make_request(piece_index: int) -> bytes:
    return encode_message(MSG_REQUEST, struct.pack(">I", piece_index))


def make_piece(piece_index: int, piece_data: bytes) -> bytes:
    return encode_message(MSG_PIECE, struct.pack(">I", piece_index) + piece_data)
