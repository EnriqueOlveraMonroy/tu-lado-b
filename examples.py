"""Local example profiles; original JSON files stay on the server."""
from dataclasses import dataclass
from pathlib import Path
import gzip

DATA_DIR = Path(__file__).parent / "data"


def available_profiles(root=None):
    base = Path(root) if root is not None else DATA_DIR
    return [f"Usuario {i}" for i in range(1, 5) if (base / f"Usuario {i}").is_dir()]


@dataclass(frozen=True)
class ExampleFile:
    path: Path

    @property
    def name(self):
        return self.path.name.removesuffix(".gz")

    def getvalue(self):
        return gzip.decompress(self.path.read_bytes()) if self.path.suffix.lower() == ".gz" else self.path.read_bytes()


def example_files(profile, video=False, root=None):
    base = Path(root) if root is not None else DATA_DIR
    if profile not in available_profiles(base):
        raise ValueError("El perfil de ejemplo no está disponible.")
    folder = (base / profile).resolve()
    prefix = "streaming_history_video_" if video else "streaming_history_audio_"
    return [ExampleFile(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and (p.name.lower().endswith(".json") or p.name.lower().endswith(".json.gz"))
            and p.name.lower().startswith(prefix)
            and p.resolve().is_relative_to(folder)]
