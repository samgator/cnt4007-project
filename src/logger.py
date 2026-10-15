"""Logging system adhering strictly to the P2P project specification.

Every log event appends to `log_peer_[peerID].log` using the exact textual structure required:
- Connection initiated: [Time]: Peer [peer_ID 1] makes a connection to Peer [peer_ID 2].
- Connection received: [Time]: Peer [peer_ID 1] is connected from Peer [peer_ID 2].
- Preferred neighbors change: [Time]: Peer [peer_ID] has the preferred neighbors [preferred neighbor ID list].
- Optimistic unchoke change: [Time]: Peer [peer_ID] has the optimistically unchoked neighbor [optimistically unchoked neighbor ID].
- Unchoked by peer: [Time]: Peer [peer_ID 1] is unchoked by [peer_ID 2].
- Choked by peer: [Time]: Peer [peer_ID 1] is choked by [peer_ID 2].
- Have received: [Time]: Peer [peer_ID 1] received the 'have' message from [peer_ID 2] for the piece [piece index].
- Interested received: [Time]: Peer [peer_ID 1] received the 'interested' message from [peer_ID 2].
- Not interested received: [Time]: Peer [peer_ID 1] received the 'not interested' message from [peer_ID 2].
- Piece downloaded: [Time]: Peer [peer_ID 1] has downloaded the piece [piece index] from [peer_ID 2]. Now the number of pieces it has is [number of pieces].
- Download complete: [Time]: Peer [peer_ID] has downloaded the complete file.
"""

from datetime import datetime
import os
from pathlib import Path
import re
import threading
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

REQUIRED_LOG_PATTERNS: List[Tuple[str, str]] = [
    (r"Peer \d+ makes a connection to Peer \d+\.", "Connection initiated"),
    (r"Peer \d+ is connected from Peer \d+\.", "Connection received"),
    (r"Peer \d+ has the preferred neighbors .*", "Preferred neighbors change"),
    (r"Peer \d+ has the optimistically unchoked neighbor \d+\.", "Optimistic unchoke change"),
    (r"Peer \d+ is unchoked by \d+\.", "Unchoked by peer"),
    (r"Peer \d+ is choked by \d+\.", "Choked by peer"),
    (r"Peer \d+ received the 'have' message from \d+ for the piece \d+\.", "Have received"),
    (r"Peer \d+ received the 'interested' message from \d+\.", "Interested received"),
    (r"Peer \d+ received the 'not interested' message from \d+\.", "Not interested received"),
    (r"Peer \d+ has downloaded the piece \d+ from \d+\. Now the number of pieces it has is \d+\.", "Piece downloaded"),
    (r"Peer \d+ has downloaded the complete file\.", "Download complete"),
]


class PeerLogger:
    """Thread-safe and process-safe logger generating exact specification-compliant log entries."""

    def __init__(
        self,
        peer_id: int,
        log_dir: Union[str, Path] = ".",
        to_stdout: bool = True,
        verbose: bool = False,
        mirror_to_root: bool = True,
    ):
        self.peer_id = peer_id
        self.to_stdout = to_stdout
        self.verbose = verbose
        self.log_dir = Path(log_dir).resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"log_peer_{peer_id}.log"
        self._lock = threading.Lock()

        # Initialize/truncate log file for a clean execution run
        self._file = open(self.log_file, "w", buffering=1, encoding="utf-8")

        # Maintain dual location (working directory + logs directory) if requested
        self._mirror_file: Optional[Path] = None
        self._mirror_handle = None
        if mirror_to_root:
            cwd = Path.cwd().resolve()
            logs_dir = cwd / "logs"

            # If writing to logs/, mirror to cwd
            if self.log_dir != cwd:
                self._mirror_file = cwd / f"log_peer_{peer_id}.log"
            # If writing to cwd, mirror to logs/ if logs/ exists
            elif logs_dir.is_dir():
                self._mirror_file = logs_dir / f"log_peer_{peer_id}.log"

            if self._mirror_file:
                try:
                    # Clean previous mirror link/file
                    if self._mirror_file.is_symlink() or self._mirror_file.is_file():
                        self._mirror_file.unlink(missing_ok=True)
                    # Attempt symlink first
                    os.symlink(self.log_file, self._mirror_file)
                except Exception:
                    # On Windows (or systems without symlink privilege), mirror via dual-write
                    try:
                        self._mirror_handle = open(self._mirror_file, "w", buffering=1, encoding="utf-8")
                    except Exception:
                        self._mirror_handle = None

    def log_connection_made(self, target_peer_id: int) -> None:
        """Connection initiated: [Time]: Peer [peer_ID 1] makes a connection to Peer [peer_ID 2]."""
        self._write_entry(f"Peer {self.peer_id} makes a connection to Peer {target_peer_id}.")

    def log_connection_received(self, source_peer_id: int) -> None:
        """Connection received: [Time]: Peer [peer_ID 1] is connected from Peer [peer_ID 2]."""
        self._write_entry(f"Peer {self.peer_id} is connected from Peer {source_peer_id}.")

 # TODO [Phase 2]: Implement unchoke, choke, have, interested, piece downloaded logs
