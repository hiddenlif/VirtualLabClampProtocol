#!/usr/bin/env python3
"""Print all public scientific metrics for one proposed protocol."""

import json
import os
from pathlib import Path

from protocol_score import evaluate


data = json.loads(Path("/app/protocol_data.json").read_text(encoding="utf-8"))
protocol_path = Path(os.environ.get("PROTOCOL_PATH", "/app/protocol.json"))
protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
print(json.dumps(evaluate(data, protocol), indent=2, sort_keys=True))

