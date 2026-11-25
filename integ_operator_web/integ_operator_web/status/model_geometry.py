"""Chassis drawing geometry read from the running Robot Model.

The status page draws the chassis from the model that the stack actually loaded, so a moved
bumper or a new wheelbase appears without editing the page. Only fixed joints are read; nothing
here decides what is installed — a missing frame simply removes its sector from the drawing.

Coordinates follow REP-103: x forward, y left. Where the model has no `ultrasonic_channel_*_link`,
`sonar` is empty and the page falls back to its placeholder layout.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Iterable, Optional

SONAR_PREFIX = "ultrasonic_channel_"
STEER_JOINTS = tuple(f"steer{index}_joint" for index in range(1, 5))


def _origin(joint: ET.Element) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    origin = joint.find("origin")
    if origin is None:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    xyz = tuple(float(value) for value in origin.get("xyz", "0 0 0").split())
    rpy = tuple(float(value) for value in origin.get("rpy", "0 0 0").split())
    return xyz, rpy


def _rotation(rpy: Iterable[float]) -> list[list[float]]:
    roll, pitch, yaw = rpy
    cr, sr, cp, sp, cy, sy = (
        math.cos(roll),
        math.sin(roll),
        math.cos(pitch),
        math.sin(pitch),
        math.cos(yaw),
        math.sin(yaw),
    )
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def _in_base(joint: ET.Element, by_child: dict) -> tuple[float, ...]:
    """Origin of `joint` in base_link with every joint at zero, through intermediate parents."""
    point, _ = _origin(joint)
    parent = joint.find("parent")
    link = parent.get("link") if parent is not None else None
    while link != "base_link":
        if link not in by_child:
            raise ValueError(f"no chain from {joint.get('name')} to base_link")
        above = by_child.pop(link)  # a cycle cannot loop forever
        xyz, rpy = _origin(above)
        rotation = _rotation(rpy)
        point = tuple(
            sum(rotation[row][k] * point[k] for k in range(3)) + xyz[row] for row in range(3)
        )
        parent = above.find("parent")
        link = parent.get("link") if parent is not None else None
    return point


def _yaw_deg(rpy: Iterable[float]) -> float:
    return round(math.degrees(tuple(rpy)[2]), 2)


def frames(urdf_text: str) -> dict:
    """Sonar frames and the steering footprint declared in one URDF document."""
    try:
        root = ET.fromstring(urdf_text)
    except ET.ParseError:
        return {"sonar": [], "wheels": [], "body": None}
    joints = {joint.get("name"): joint for joint in root.findall("joint")}
    sonar = []
    for name, joint in joints.items():
        if not name or not name.startswith(SONAR_PREFIX) or joint.get("type") != "fixed":
            continue
        channel = name[len(SONAR_PREFIX) :].split("_", 1)[0]
        if not channel.isdigit():
            continue
        xyz, rpy = _origin(joint)
        sonar.append(
            {"channel": int(channel), "x_m": xyz[0], "y_m": xyz[1], "yaw_deg": _yaw_deg(rpy)}
        )
    sonar.sort(key=lambda item: item["channel"])

    by_child = {
        joint.find("child").get("link"): joint
        for joint in root.findall("joint")
        if joint.find("child") is not None
    }
    wheels = []
    for name in STEER_JOINTS:
        if name in joints:
            # Rear modules may hang below the suspension rather than directly on base_link.
            try:
                x, y, _ = _in_base(joints[name], dict(by_child))
            except ValueError:
                continue
            wheels.append({"joint": name, "x_m": round(x, 6), "y_m": round(y, 6)})
    body = None
    if wheels:
        half_length = max(abs(item["x_m"]) for item in wheels)
        half_width = max(abs(item["y_m"]) for item in wheels)
        body = {"half_length_m": round(half_length, 4), "half_width_m": round(half_width, 4)}
    return {"sonar": sonar, "wheels": wheels, "body": body}


def parse(urdf_path: Optional[str]) -> dict:
    """`frames` for a model file; an unreadable or missing file yields the empty drawing."""
    if not urdf_path:
        return {"sonar": [], "wheels": [], "body": None}
    try:
        from pathlib import Path

        return frames(Path(urdf_path).read_text(encoding="utf-8"))
    except OSError:
        return {"sonar": [], "wheels": [], "body": None}


__all__ = ["SONAR_PREFIX", "STEER_JOINTS", "frames", "parse"]
