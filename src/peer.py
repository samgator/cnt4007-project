"""Core BitTorrent-like Peer engine implementing asynchronous networking.

Provides:
- Asynchronous TCP listening server for subsequent peers in topology.
- Concurrent client connection initiation tasks for prior peers.
- Connection state tracking and graceful process shutdown.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

try:
    from .config import CommonConfig, PeerInfo
    from .logger import PeerLogger
    from .protocol import make_handshake, parse_handshake
except ImportError:
    from config import CommonConfig, PeerInfo
    from logger import PeerLogger
    from protocol import make_handshake, parse_handshake


class PeerProcess:
    """Represents an active peer node in the P2P file sharing mesh."""

    def __init__(
        self,
        peer_id: int,
        common_cfg: CommonConfig,
        peer_info_list: List[PeerInfo],
        base_dir: Union[str, Path] = ".",
        log_dir: Optional[Union[str, Path]] = None,
        verbose: bool = False,
    ):
        self.peer_id = peer_id
        self.common_cfg = common_cfg
        self.peer_info_list = peer_info_list
        self.base_dir = Path(base_dir).resolve()
        self.verbose = verbose

        # Locate own peer info
        self.my_info: Optional[PeerInfo] = None
        self.my_index = -1
        for idx, info in enumerate(self.peer_info_list):
            if info.peer_id == self.peer_id:
                self.my_info = info
                self.my_index = idx
                break

        if self.my_info is None:
            raise ValueError(f"Peer ID {self.peer_id} not found in PeerInfo.cfg")

        # Partition peers according to sequential startup topology
        self.prior_peers = self.peer_info_list[: self.my_index]
        self.subsequent_peers = self.peer_info_list[self.my_index + 1 :]
        self.all_peer_ids: Set[int] = {p.peer_id for p in self.peer_info_list}

        # Initialize logging
        target_log_dir = log_dir if log_dir is not None else self.base_dir
        self.logger = PeerLogger(self.peer_id, log_dir=target_log_dir, verbose=self.verbose)
        if not hasattr(self.logger, "_write_entry"):
            def _fallback_write(msg: str, *args, **kwargs):
                entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {msg}\n"
                with self.logger._lock:
                    self.logger._file.write(entry)
                    self.logger._file.flush()
                if self.logger.to_stdout:
                    print(f"[{self.peer_id}] {entry.strip()}", flush=True)
            self.logger._write_entry = _fallback_write

        # Connection and socket state
        self.connected_peers: Set[int] = set()
        self.peer_writers: Dict[int, asyncio.StreamWriter] = {}
        self.peer_readers: Dict[int, asyncio.StreamReader] = {}

        # Lifecycle and background tasks
        self.stop_event = asyncio.Event()
        self.server: Optional[asyncio.Server] = None
        self.background_tasks: List[asyncio.Task] = []
        self.is_terminating = False

    async def start(self) -> None:
        """Starts listening server and connects to prior peers."""
        # 1. Start listening server
        listen_host = "0.0.0.0"
        self.server = await asyncio.start_server(
            self._handle_incoming_connection,
            listen_host,
            self.my_info.port,
            reuse_address=True,
        )
        print(f"[{self.peer_id}] Server listening on {listen_host}:{self.my_info.port}", flush=True)

        # 2. Concurrently initiate TCP connections to all peers listed before it
        for target in self.prior_peers:
            task = asyncio.create_task(self._connect_to_prior_peer(target))
            self.background_tasks.append(task)

        # Wait until termination condition triggers
        await self.stop_event.wait()
        await self._shutdown()

    async def _connect_to_prior_peer(self, target: PeerInfo) -> None:
        """Retries connecting to a prior peer until successful or terminated."""
        while not self.stop_event.is_set():
            try:
                reader, writer = await asyncio.open_connection(target.hostname, target.port)

                # Send 32-byte handshake
                handshake_out = make_handshake(self.peer_id)
                writer.write(handshake_out)
                await writer.drain()

                # Read 32-byte handshake
                handshake_in = await reader.readexactly(32)
                valid, remote_id = parse_handshake(handshake_in)
                if not valid or remote_id != target.peer_id:
                    writer.close()
                    await writer.wait_closed()
                    await asyncio.sleep(0.3)
                    continue

                # Log connection initiated
                self.logger.log_connection_made(target.peer_id)

                self.connected_peers.add(target.peer_id)
                self.peer_readers[target.peer_id] = reader
                self.peer_writers[target.peer_id] = writer
                break
            except (ConnectionRefusedError, OSError, asyncio.IncompleteReadError):
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(0.3)

    async def _handle_incoming_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handles an incoming TCP connection accepted by the server."""
        try:
            # Read 32-byte handshake
            handshake_in = await reader.readexactly(32)
            valid, remote_id = parse_handshake(handshake_in)
            if not valid or remote_id not in self.all_peer_ids:
                writer.close()
                await writer.wait_closed()
                return

            # Send 32-byte handshake back
            handshake_out = make_handshake(self.peer_id)
            writer.write(handshake_out)
            await writer.drain()

            # Log connection received
            self.logger.log_connection_received(remote_id)

            self.connected_peers.add(remote_id)
            self.peer_readers[remote_id] = reader
            self.peer_writers[remote_id] = writer
        except Exception as e:
            print(f"[{self.peer_id}] Incoming connection exception: {type(e)} {e}", flush=True)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _shutdown(self) -> None:
        """Gracefully closes server, sockets, and logger."""
        print(f"[{self.peer_id}] Gracefully shutting down peer process...", flush=True)

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        for writer in list(self.peer_writers.values()):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        if hasattr(self.logger, "close"):
            self.logger.close()
        elif hasattr(self.logger, "_file"):
            try:
                self.logger._file.close()
            except Exception:
                pass
        print(f"[{self.peer_id}] Peer process cleanly terminated.", flush=True)
