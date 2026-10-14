#!/usr/bin/env python3
"""Main entry point for BitTorrent-like Peer process.

Usage:
    python3 peerProcess.py [peerID]
    ./peerProcess [peerID]
"""

import argparse
import asyncio
import os
from pathlib import Path
import sys

# Ensure src/ is importable
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from src.config import parse_common_config, parse_peer_info
    from src.peer import PeerProcess
except ImportError:
    from config import parse_common_config, parse_peer_info
    from peer import PeerProcess


def main() -> int:
    parser = argparse.ArgumentParser(description="BitTorrent-like P2P File Sharing Peer Process")
    parser.add_argument("peer_id", type=int, help="Peer ID as defined in PeerInfo.cfg")
    parser.add_argument(
        "--config-dir",
        type=str,
        default=".",
        help="Directory containing Common.cfg and PeerInfo.cfg (default: current directory)",
    )
    parser.add_argument(
        "--common-cfg",
        type=str,
        default=None,
        help="Path to Common.cfg (default: [config-dir]/Common.cfg)",
    )
    parser.add_argument(
        "--peer-info-cfg",
        type=str,
        default=None,
        help="Path to PeerInfo.cfg (default: [config-dir]/PeerInfo.cfg)",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory to write logs into (default: current directory or logs/)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose stdout logging for every piece download and have event",
    )

    args = parser.parse_args()

    config_dir = Path(args.config_dir).resolve()
    common_cfg_path = Path(args.common_cfg).resolve() if args.common_cfg else config_dir / "Common.cfg"
    peer_info_cfg_path = Path(args.peer_info_cfg).resolve() if args.peer_info_cfg else config_dir / "PeerInfo.cfg"

    # Fallback to config/ directories if not present in current working directory
    if not common_cfg_path.exists():
        for fallback in [
            ROOT_DIR / "config" / "Common.cfg",
            ROOT_DIR / "config" / "local" / "Common.cfg",
        ]:
            if fallback.exists():
                common_cfg_path = fallback
                break

    if not peer_info_cfg_path.exists():
        for fallback in [
            ROOT_DIR / "config" / "PeerInfo.cfg",
            ROOT_DIR / "config" / "local" / "PeerInfo.cfg",
        ]:
            if fallback.exists():
                peer_info_cfg_path = fallback
                break

    if not common_cfg_path.exists():
        print(f"Error: Common.cfg not found at {common_cfg_path} (checked {config_dir} and config/)", file=sys.stderr)
        return 1

    if not peer_info_cfg_path.exists():
        print(f"Error: PeerInfo.cfg not found at {peer_info_cfg_path} (checked {config_dir} and config/)", file=sys.stderr)
        return 1

    try:
        common_cfg = parse_common_config(common_cfg_path)
        peer_info_list = parse_peer_info(peer_info_cfg_path)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Instantiate and run peer process
    peer = PeerProcess(
        peer_id=args.peer_id,
        common_cfg=common_cfg,
        peer_info_list=peer_info_list,
        base_dir=config_dir,
        log_dir=args.log_dir,
        verbose=args.verbose,
    )

    try:
        asyncio.run(peer.start())
        return 0
    except KeyboardInterrupt:
        print(f"\n[Peer {args.peer_id}] Terminated by keyboard interrupt.", flush=True)
        return 0
    except Exception as e:
        print(f"[Peer {args.peer_id}] Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
