import importlib.util
import os
import random

from mev import detect

_spec = importlib.util.spec_from_file_location(
    "multi_scan", os.path.join(os.path.dirname(__file__), "..", "scripts", "multi_scan.py"))
multi_scan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(multi_scan)


def test_block_filter_never_changes_detection():
    """keep_block may only drop blocks in which detect finds nothing."""
    rng = random.Random(7)
    senders = [f"0xu{i}" for i in range(4)] + ["0xatk"]
    found = 0
    for _ in range(3000):
        n = rng.randint(1, 7)
        meta, swaps = {}, []
        for k in range(n):
            tx = f"t{k}"
            sender = rng.choice(senders)
            meta[tx] = (sender, "0xbot" if sender == "0xatk" else rng.choice(["0xr1", "0xr2"]))
            size = rng.choice([100, 100, 101, 95, 60])
            swaps.append(dict(tx=tx, log_index=k, block=1,
                              **(dict(amount0=-size // 10, amount1=size) if rng.random() < .5
                                 else dict(amount0=size // 10, amount1=-size))))
        full = detect.detect_block(1, swaps, meta)
        found += bool(full)
        if not multi_scan.keep_block(swaps):
            assert full == []
    assert found > 50  # the random blocks do contain sandwiches, so the check is not vacuous
