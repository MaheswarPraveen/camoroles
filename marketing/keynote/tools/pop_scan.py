"""Scan a rendered film for single-frame pops: frame-difference spikes > 3x both neighbours."""
import subprocess
import sys

import numpy as np

path = sys.argv[1]
W, H = 135, 240                       # small grayscale frames are enough to find jumps
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))      # diff[i] = change from frame i to i+1
flag = []
for i in range(1, len(diff) - 1):
    neigh = max(diff[i - 1], diff[i + 1], 0.3)
    if diff[i] > 3 * neigh and diff[i] > 2.0:
        flag.append((i + 1, diff[i], diff[i - 1], diff[i + 1]))
print(f"{len(frames)} frames, mean change {diff.mean():.2f}, max {diff.max():.2f}")
for n, d, a, b in flag:
    print(f"pop at frame {n} (t={n / 60:.3f}s, beat {n / 30:.2f}): {d:.1f} vs neighbours {a:.1f}/{b:.1f}")
print("pops:", len(flag))
