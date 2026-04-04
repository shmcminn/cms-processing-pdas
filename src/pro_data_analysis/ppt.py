from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .models import Metadata

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_pptx(
    metadata: Metadata,
    slide_images: list[Path],
    output_path: Path,
    workspace_dir: Path,
) -> None:
    payload = {
        "title": metadata.title,
        "byline": metadata.byline.upper(),
        "date": metadata.date_mmddyyyy,
        "dek": metadata.dek,
        "source": metadata.source,
        "slide_images": [str(path) for path in slide_images],
        "output_path": str(output_path),
    }
    payload_path = workspace_dir / "ppt_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2))
    node_binary = shutil.which("node")
    if node_binary is None:
        raise RuntimeError("Node is required to build the PowerPoint deck.")
    subprocess.run(
        [node_binary, str(REPO_ROOT / "tools" / "build_pptx.mjs"), str(payload_path)],
        cwd=REPO_ROOT,
        check=True,
    )
