"""Comprehensive unit tests for configuration, wire protocol, and file management."""

import io
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from src.config import CommonConfig, PeerInfo, parse_common_config, parse_peer_info
    from src.file_manager import FileManager, compute_sha256
    from src.protocol import (
        HANDSHAKE_HEADER,
        HANDSHAKE_TOTAL_LEN,
        MSG_BITFIELD,
        MSG_CHOKE,
        MSG_HAVE,
        MSG_INTERESTED,
        MSG_NOT_INTERESTED,
        MSG_PIECE,
        MSG_REQUEST,
        MSG_UNCHOKE,
        encode_message,
        make_bitfield,
        make_choke,
        make_handshake,
        make_have,
        make_interested,
        make_not_interested,
        make_piece,
        make_request,
        make_unchoke,
        parse_bitfield,
        parse_handshake,
    )
except ImportError:
    from config import CommonConfig, PeerInfo, parse_common_config, parse_peer_info
    from file_manager import FileManager, compute_sha256
    from protocol import (
        HANDSHAKE_HEADER,
        HANDSHAKE_TOTAL_LEN,
        MSG_BITFIELD,
        MSG_CHOKE,
        MSG_HAVE,
        MSG_INTERESTED,
        MSG_NOT_INTERESTED,
        MSG_PIECE,
        MSG_REQUEST,
        MSG_UNCHOKE,
        encode_message,
        make_bitfield,
        make_choke,
        make_handshake,
        make_have,
        make_interested,
        make_not_interested,
        make_piece,
        make_request,
        make_unchoke,
        parse_bitfield,
        parse_handshake,
    )


class TestConfigParsing(unittest.TestCase):

    def test_parse_common_config(self):
        content = """
        NumberOfPreferredNeighbors 3
        UnchokingInterval 5
        OptimisticUnchokingInterval 10
        FileName test_file.dat
        FileSize 100000
        PieceSize 16384
        """
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(content)
            temp_name = f.name

        try:
            cfg = parse_common_config(temp_name)
            self.assertEqual(cfg.num_preferred_neighbors, 3)
            self.assertEqual(cfg.unchoking_interval, 5.0)
            self.assertEqual(cfg.optimistic_unchoking_interval, 10.0)
            self.assertEqual(cfg.file_name, "test_file.dat")
            self.assertEqual(cfg.file_size, 100000)
            self.assertEqual(cfg.piece_size, 16384)
            self.assertEqual(cfg.num_pieces, math.ceil(100000 / 16384))
            # Test piece size calculations
            self.assertEqual(cfg.piece_size_for_index(0), 16384)
            last_idx = cfg.num_pieces - 1
            expected_last_size = 100000 - (last_idx * 16384)
            self.assertEqual(cfg.piece_size_for_index(last_idx), expected_last_size)
        finally:
            os.remove(temp_name)

    def test_parse_peer_info(self):
        content = """
        1001 127.0.0.1 6001 1
        1002 127.0.0.1 6002 0
        1003 127.0.0.1 6003 0
        """
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(content)
            temp_name = f.name

        try:
            peers = parse_peer_info(temp_name)
            self.assertEqual(len(peers), 3)
            self.assertEqual(peers[0], PeerInfo(1001, "127.0.0.1", 6001, True))
            self.assertEqual(peers[1], PeerInfo(1002, "127.0.0.1", 6002, False))
            self.assertEqual(peers[2], PeerInfo(1003, "127.0.0.1", 6003, False))
        finally:
            os.remove(temp_name)


class TestProtocol(unittest.TestCase):

    def test_handshake(self):
        hs = make_handshake(1001)
        self.assertEqual(len(hs), HANDSHAKE_TOTAL_LEN)
        self.assertEqual(hs[:18], HANDSHAKE_HEADER)
        self.assertEqual(hs[18:28], b"\x00" * 10)
        self.assertEqual(struct.unpack(">I", hs[28:32])[0], 1001)

        valid, peer_id = parse_handshake(hs)
        self.assertTrue(valid)
        self.assertEqual(peer_id, 1001)

        # Invalid header
        invalid_hs = b"X" * 18 + b"\x00" * 10 + struct.pack(">I", 1001)
        valid, _ = parse_handshake(invalid_hs)
        self.assertFalse(valid)

    def test_standard_messages(self):
        # Choke
        m_choke = make_choke()
        self.assertEqual(len(m_choke), 5)
        length, msg_type = struct.unpack(">IB", m_choke)
        self.assertEqual(length, 1)
        self.assertEqual(msg_type, MSG_CHOKE)

        # Unchoke
        m_unchoke = make_unchoke()
        length, msg_type = struct.unpack(">IB", m_unchoke)
        self.assertEqual(length, 1)
        self.assertEqual(msg_type, MSG_UNCHOKE)

        # Interested
        m_int = make_interested()
        length, msg_type = struct.unpack(">IB", m_int)
        self.assertEqual(length, 1)
        self.assertEqual(msg_type, MSG_INTERESTED)

        # Not Interested
        m_not_int = make_not_interested()
        length, msg_type = struct.unpack(">IB", m_not_int)
        self.assertEqual(length, 1)
        self.assertEqual(msg_type, MSG_NOT_INTERESTED)

        # Have
        m_have = make_have(42)
        length, msg_type, p_idx = struct.unpack(">IBI", m_have)
        self.assertEqual(length, 5)
        self.assertEqual(msg_type, MSG_HAVE)
        self.assertEqual(p_idx, 42)

        # Request
        m_req = make_request(15)
        length, msg_type, p_idx = struct.unpack(">IBI", m_req)
        self.assertEqual(length, 5)
        self.assertEqual(msg_type, MSG_REQUEST)
        self.assertEqual(p_idx, 15)

        # Piece
        piece_bytes = b"Hello, P2P World!"
        m_piece = make_piece(7, piece_bytes)
        length, msg_type, p_idx = struct.unpack(">IBI", m_piece[:9])
        self.assertEqual(length, 1 + 4 + len(piece_bytes))
        self.assertEqual(msg_type, MSG_PIECE)
        self.assertEqual(p_idx, 7)
        self.assertEqual(m_piece[9:], piece_bytes)

    def test_bitfield(self):
        total_pieces = 19
        pieces_set = {0, 3, 7, 8, 18}
        bf = make_bitfield(pieces_set, total_pieces)
        self.assertEqual(len(bf), math.ceil(19 / 8))  # 3 bytes

        # Check Byte 0: indices 0..7. Indices 0, 3, 7 are set.
        # Bit 7 (piece 0), Bit 4 (piece 3), Bit 0 (piece 7)
        # 10010001 in binary = 0x91 = 145
        self.assertEqual(bf[0], 0b10010001)

        # Check Byte 1: indices 8..15. Index 8 is set.
        # Bit 7 (piece 8) -> 10000000 = 0x80 = 128
        self.assertEqual(bf[1], 0b10000000)

        # Check Byte 2: indices 16..23. Index 18 is set.
        # Bit 5 (piece 18) -> 00100000 = 0x20 = 32
        self.assertEqual(bf[2], 0b00100000)

        # Parse back
        parsed = parse_bitfield(bf, total_pieces)
        self.assertEqual(parsed, pieces_set)


class TestFileManager(unittest.TestCase):

    def test_slicing_and_reassembly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            file_size = 50000
            piece_size = 16384
            file_name = "test_data.bin"

            # Create dummy source file
            dummy_content = os.urandom(file_size)
            source_dir = base_dir / "peer_1001"
            source_dir.mkdir(parents=True)
            source_file = source_dir / file_name
            with open(source_file, "wb") as f:
                f.write(dummy_content)

            cfg = CommonConfig(
                num_preferred_neighbors=2,
                unchoking_interval=5.0,
                optimistic_unchoking_interval=10.0,
                file_name=file_name,
                file_size=file_size,
                piece_size=piece_size,
            )

            # Seeder file manager
            seeder_fm = FileManager(1001, cfg, base_dir=base_dir)
            seeder_fm.initialize_storage(has_file=True)
            self.assertEqual(len(seeder_fm.downloaded_indices), cfg.num_pieces)

            # Leecher file manager
            leecher_fm = FileManager(1002, cfg, base_dir=base_dir)
            leecher_fm.initialize_storage(has_file=False)
            self.assertEqual(len(leecher_fm.downloaded_indices), 0)

            # Transfer all pieces from seeder to leecher
            for i in range(cfg.num_pieces):
                data = seeder_fm.get_piece(i)
                self.assertIsNotNone(data)
                stored = leecher_fm.store_piece(i, data)
                self.assertTrue(stored)

            # Reassemble file on leecher
            leecher_hash = leecher_fm.assemble_and_save_file()
            source_hash = compute_sha256(source_file)
            self.assertEqual(leecher_hash, source_hash)


if __name__ == "__main__":
    unittest.main()
