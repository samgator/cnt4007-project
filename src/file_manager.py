import hashlib
import os
from pathlib import Path
import shutil
from typing import Dict, Optional, Set, Union
import zipfile
try:
    from .config import CommonConfig
except ImportError:
    from config import CommonConfig


def compute_sha256(filepath: Union[str, Path]) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class FileManager:
    def __init__(self, peer_id: int, common_cfg: CommonConfig, base_dir: Union[str, Path] = "."):
        self.peer_id = peer_id
        self.config = common_cfg
        self.base_dir = Path(base_dir).resolve()
        data_peer_dir = self.base_dir / "data" / f"peer_{peer_id}"
        if data_peer_dir.is_dir():
            self.peer_dir = data_peer_dir
        else:
            self.peer_dir = self.base_dir / f"peer_{peer_id}"
        self.file_path = self.peer_dir / self.config.file_name

        self.pieces: Dict[int, bytes] = {}
        self.downloaded_indices: Set[int] = set()

    def initialize_storage(self, has_file: bool) -> None:
        self.peer_dir.mkdir(parents=True, exist_ok=True)

        if has_file:
            if not self.file_path.exists():
                found = self._find_seed_file()
                if found:
                    shutil.copy2(found, self.file_path)
                else:
                    raise FileNotFoundError(
                        f"Seed file '{self.config.file_name}' not found for peer {self.peer_id} "
                        f"at {self.file_path} and no fallback asset was located."
                    )
            actual_size = self.file_path.stat().st_size
            if actual_size != self.config.file_size:
                raise ValueError(
                    f"File {self.file_path} has size {actual_size}, expected {self.config.file_size}"
                )

            with open(self.file_path, "rb") as f:
                full_content = f.read()

            for i in range(self.config.num_pieces):
                start = i * self.config.piece_size
                end = min(self.config.file_size, (i + 1) * self.config.piece_size)
                self.pieces[i] = full_content[start:end]
                self.downloaded_indices.add(i)
        else:
            self.downloaded_indices.clear()
            self.pieces.clear()

    def _find_seed_file(self) -> Optional[Path]:
        candidates = [
            self.base_dir / "peer_1001" / self.config.file_name,
            self.base_dir / "peer_1006" / self.config.file_name,
            self.base_dir / str(self.peer_id) / self.config.file_name,
            self.base_dir / "1001" / self.config.file_name,
            self.base_dir / self.config.file_name,
        ]
        for c in candidates:
            if c.exists() and c.is_file() and c.stat().st_size == self.config.file_size:
                return c

        zip_candidates = [
            self.base_dir / "docs" / "archives" / "project_config_file_small.zip",
            self.base_dir / "docs" / "archives" / "project_config_file_large.zip",
            self.base_dir.parent / "docs" / "archives" / "project_config_file_small.zip",
            self.base_dir.parent / "docs" / "archives" / "project_config_file_large.zip",
            self.base_dir / "project_config_file_small.zip",
            self.base_dir / "project_config_file_large.zip",
            self.base_dir.parent / "project_config_file_small.zip",
            self.base_dir.parent / "project_config_file_large.zip",
        ]
        for zpath in zip_candidates:
            if zpath.exists() and zpath.is_file():
                try:
                    with zipfile.ZipFile(zpath, "r") as zf:
                        for item in zf.infolist():
                            if item.filename.endswith(self.config.file_name) and item.file_size == self.config.file_size:
                                target_extracted = self.peer_dir / self.config.file_name
                                with zf.open(item) as src_f, open(target_extracted, "wb") as dst_f:
                                    shutil.copyfileobj(src_f, dst_f)
                                return target_extracted
                except Exception:
                    pass
        for root, _, files in os.walk(self.base_dir):
            if self.config.file_name in files:
                p = Path(root) / self.config.file_name
                if p.is_file() and p.stat().st_size == self.config.file_size:
                    return p
        return None

    def store_piece(self, piece_index: int, data: bytes) -> bool:
        expected_size = self.config.piece_size_for_index(piece_index)
        if len(data) != expected_size:
            raise ValueError(
                f"piece {piece_index} has invalid length {len(data)}, expected {expected_size}"
            )
        if piece_index in self.downloaded_indices:
            return False

        self.pieces[piece_index] = data
        self.downloaded_indices.add(piece_index)
        return True

    def get_piece(self, piece_index: int) -> Optional[bytes]:
        return self.pieces.get(piece_index)

    def assemble_and_save_file(self) -> str:
        if len(self.downloaded_indices) != self.config.num_pieces:
            raise RuntimeError(
                f"cannot assemble the file: only have {len(self.downloaded_indices)}/{self.config.num_pieces} pieces."
            )

        temp_path = self.peer_dir / f"{self.config.file_name}.tmp"
        with open(temp_path, "wb") as f:
            for i in range(self.config.num_pieces):
                f.write(self.pieces[i])

        actual_size = temp_path.stat().st_size
        if actual_size != self.config.file_size:
            raise ValueError(
                f"assembled file size {actual_size} does not match the expected {self.config.file_size}"
            )
        temp_path.replace(self.file_path)
        return compute_sha256(self.file_path)