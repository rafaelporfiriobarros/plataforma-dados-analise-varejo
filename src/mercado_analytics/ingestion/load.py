import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mercado_analytics.config import RAW_DIR


@dataclass(frozen=True)
class RawBatch:
    dataset: str
    path: Path
    batch_id: str

    @property
    def source_file(self) -> str:
        return self.path.name

    @property
    def file_hash(self) -> str:

        digest = hashlib.sha256()
        with self.path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


def _batch_id(path: Path) -> str:

    ranges = re.findall(r"(20\d{2})[_-](0[1-9]|1[0-2])", path.stem)
    if not ranges:
        raise ValueError(
            f"Arquivo RAW sem período no nome: {path.name}. Use YYYY_MM para "
            "cargas mensais ou YYYY_MM_YYYY_MM para uma carga histórica."
        )
    periods = [f"{year}-{month}" for year, month in ranges]
    return periods[0] if len(periods) == 1 else f"{periods[0]}_{periods[-1]}"


def discover_raw_batches() -> list[RawBatch]:
    batches: list[RawBatch] = []
    patterns = {
        "cards": [RAW_DIR / "vendas_cartoes", RAW_DIR],
        "hourly": [RAW_DIR / "vendas_por_horario", RAW_DIR],
    }
    prefixes = {"cards": "vendas_cartoes_", "hourly": "vendas_por_horario_"}

    for dataset, folders in patterns.items():
        seen: set[Path] = set()
        for folder in folders:
            if not folder.exists():
                continue
            for path in sorted(folder.glob(f"{prefixes[dataset]}*.csv")):
                if path in seen:
                    continue
                seen.add(path)
                batches.append(RawBatch(dataset, path, _batch_id(path)))
    return sorted(batches, key=lambda b: (b.batch_id, b.dataset, b.source_file))


def load_batch(batch: RawBatch) -> pd.DataFrame:
    return pd.read_csv(batch.path, sep=";")


def load_raw_data():

    cards = pd.read_csv(RAW_DIR / "vendas_cartoes.csv", sep=";")
    hourly = pd.read_csv(RAW_DIR / "vendas_por_horario.csv", sep=";")
    return cards, hourly
