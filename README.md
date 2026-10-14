# CNT4007 P2P File Sharing Project (BitTorrent)

A BitTorrent-like peer-to-peer (P2P) file sharing protocol implementation in Python for UF CNT4007.

## Team Members
- **Sam Morsics** - UFID: 85201061
- **Bora Turkmen** - UFID: 25221169
- **Jayden Ollis** - UFID: 61598910

## Project Structure
```text
.
├── src/        # Core protocol and networking source code
├── config/     # Configuration files and topologies (Common.cfg, PeerInfo.cfg)
├── docs/       # Project specifications, sample code, and references
├── scripts/    # Utility and operational scripts
└── tests/      # Unit and integration test suites
```

## Getting Started
This project requires Python 3.8+.

To run a peer process, execute `./peerProcess <peerID>` (or `python3 peerProcess.py <peerID>`, or `peerProcess <peerID>` on Windows).
