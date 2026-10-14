import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

@dataclass
class CommonConfig:
    num_preferred_neighbors: int
    unchoking_interval: float
    optimistic_unchoking_interval: float
    file_name: str
    file_size: int
    piece_size: int

    @property
    def num_pieces(self) -> int:
        return math.ceil(self.file_size / self.piece_size)

    def piece_size_for_index(self, piece_index: int) -> int:
        if piece_index < 0 or piece_index >= self.num_pieces:
            raise IndexError(f"Piece index {piece_index} out of range (0... {self.num_pieces - 1})")
        start = piece_index * self.piece_size
        end = min(self.file_size, (piece_index + 1) * self.piece_size)
        return end - start

@dataclass
class PeerInfo:
    peer_id: int
    hostname: str
    port: int
    has_file: bool

def parse_common_config(filepath: Union[str, Path]) -> CommonConfig:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Common.cfg could not be found at: {path.resolve()}")

    params: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                params[key] = val

    required_keys = ["NumberOfPreferredNeighbors", "UnchokingInterval", "OptimisticUnchokingInterval", "FileName", "FileSize", "PieceSize",]
    missing = [k for k in required_keys if k not in params]
    if missing:
        raise ValueError(f"Missing required keys in Common.cfg: {missing}")

    return CommonConfig(
        num_preferred_neighbors=int(params["NumberOfPreferredNeighbors"]),
        unchoking_interval=float(params["UnchokingInterval"]),
        optimistic_unchoking_interval=float(params["OptimisticUnchokingInterval"]),
        file_name=params["FileName"],
        file_size=int(params["FileSize"]),
        piece_size=int(params["PieceSize"]),
    )

def parse_peer_info(filepath: Union[str, Path]) -> List[PeerInfo]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PeerInfo.cfg could not be found at: {path.resolve()}")

    peers: List[PeerInfo] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            peer_id = int(parts[0])
            hostname = parts[1]
            port = int(parts[2])
            has_file = int(parts[3]) == 1
            peers.append(PeerInfo(peer_id=peer_id, hostname=hostname, port=port, has_file=has_file))

    if not peers:
        raise ValueError(f"no valid peer records found in {path.resolve()}")

    return peers