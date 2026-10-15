# CNT4007 P2P File Sharing Project (BitTorrent)

A BitTorrent-like peer-to-peer (P2P) file sharing protocol implementation in Python for UF CNT4007.


## Team Members
- **Sam Morsics** - UFID: 85201061
- **Bora Turkmen** - UFID: 25221169
- **Jayden Ollis** - UFID: 61598910

## Midpoint Checkpoint Status

This repository contains our team's Midpoint Checkpoint Deliverable with ~850 lines of compilable code.

### Accomplished Milestones:
1. **Dynamic Configuration Parsing (`src/config.py`)**:
2. **Wire Framing & Handshake (`src/protocol.py`)**:
3. **Event Logger (`src/logger.py`)**:
4. **Storage & Slicing (`src/file_manager.py`)**:
5. **Core Asynchronous Network Engine (`src/peer.py`)**:
6. **Cross-Platform CLI & Wrappers (`peerProcess.py`, `peerProcess`, `peerProcess.bat`)**:

## Project Structure
```text
.
├── peerProcess                # Root executable bash wrapper (Linux/macOS)
├── peerProcess.bat            # Root executable batch wrapper (Windows)
├── peerProcess.py             # Root CLI entry point
├── Common.cfg                 # Active Common configuration file
├── PeerInfo.cfg               # Active PeerInfo topology file
├── README.md                  # Team and project documentation
├── .gitignore                 # Python bytecode and temporary log ignore rules
├── src/                       # Core protocol and networking source code
│   ├── config.py              # Dynamic configuration parser
│   ├── file_manager.py        # File slicing and storage manager
│   ├── logger.py              # Specification event logger
│   ├── peer.py                # Asynchronous network engine & handshake state machine
│   └── protocol.py            # 32-byte handshake, wire framing, bitfield
├── config/                    # Configuration files and topologies
│   ├── Common.cfg
│   └── PeerInfo.cfg
├── docs/                      # Course specifications and reference documents
│   ├── project description-v1.pdf
│   ├── project logistics-v1.pdf
│   ├── Sample Client.java
│   ├── Sample Server.java
│   └── archives/              # Sample config and asset archives
├── scripts/                   # Operational and utility scripts
└── tests/                     # Test suites
    └── test_units.py          # Unit tests for protocol, config, and bitfield
```

## Getting Started

### Prerequisites
- Python 3.8 or higher (uses standard library modules: `asyncio`, `struct`, `socket`, `pathlib`).


## How to Run the Program

Peers can be started using either the executable wrapper or directly via Python.

### 1. Running on Linux / macOS
```bash
# Using the executable wrapper:
./peerProcess <peerID>

# Or invoking Python directly:
python3 peerProcess.py <peerID>
```

### 2. Running on Windows
```cmd
Command Prompt:
peerProcess <peerID>

or

python peerProcess.py <peerID>

PowerShell:
.\peerProcess <peerID>
```

### Optional Command-Line Arguments
```text
positional arguments:
  peer_id               Peer ID as defined in PeerInfo.cfg

options:
  -h, --help            Show help message and exit
  --config-dir DIR      Directory containing Common.cfg and PeerInfo.cfg (default: current directory, fallback to config/)
  --common-cfg FILE     Custom path to Common.cfg
  --peer-info-cfg FILE  Custom path to PeerInfo.cfg
  --log-dir DIR         Directory to write log files into (default: current directory)
  --verbose, -v         Enable verbose stdout logging
```

## Midpoint Checkpoint Verification

To verify the midpoint functionality:

### Step 1: Start First Peer
Open a terminal and start Peer `1001` (configured to listen on port `6001`):
```bash
./peerProcess 1001
```
Output:
```text
[1001] Server listening on 0.0.0.0:6001
```

### Step 2: Start Second Peer
Open a second terminal in the same directory and start Peer `1002` (configured to listen on port `6002` and connect to prior peer `1001`):
```bash
./peerProcess 1002
```

### Expected Output
**Terminal 1 (Peer 1001):**
```text
[1001] Server listening on 0.0.0.0:6001
[1001] 2026-10-14 21:19:44: Peer 1001 is connected from Peer 1002.
```

**Terminal 2 (Peer 1002):**
```text
[1002] Server listening on 0.0.0.0:6002
[1002] 2026-10-14 21:19:44: Peer 1002 makes a connection to Peer 1001.
```

**Log Files:**

Written to root project directory.

### Step 3: Inspect Generated Log Files
Both peers automatically generate specification-compliant log files in the current working directory:
```bash
cat log_peer_1001.log
# 2026-10-14 21:19:44: Peer 1001 is connected from Peer 1002.

cat log_peer_1002.log
# 2026-10-14 21:19:44: Peer 1002 makes a connection to Peer 1001.
```

## Running Unit Tests

To run the unit test suite covering configuration parsing, wire framing, and handshake serialization:
```bash
python3 -m unittest discover tests/
```
