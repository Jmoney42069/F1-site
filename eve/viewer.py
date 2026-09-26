#!/usr/bin/env python3
"""Writes eve/out/viewer.html from eve/out/eve_v0.glb."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad", "model"))
from viewer import make_viewer  # noqa: E402

GROUPS = [["Hoofd", ["head", "visor", "eye"], "#e9eef2"], ["Lijf", ["body"], "#dfe5ea"],
          ["Armen", ["arm_"], "#cfd8de"], ["Benen", ["leg_"], "#bfc9d0"]]
make_viewer(os.path.join(HERE, "out", "eve_v0.glb"), os.path.join(HERE, "out", "viewer.html"),
            "EVE-bot 3D", "EVE-bot, vormstudie v1",
            "Alleen de buitenvorm, nog geen binnenkant. Tik een groep aan om hem te verbergen.",
            "≈150 × 200 × 365 mm", GROUPS, cam="620,360,380", tgt="0,190,0")
print("wrote eve/out/viewer.html")
