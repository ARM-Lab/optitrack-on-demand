from dataclasses import dataclass

@dataclass(frozen=True)
class MocapSample:
    timestamp: float
    rigid_body_name: str
    x: float
    y: float
    z: float

    m1x: float | None = None
    m1y: float | None = None
    m1z: float | None = None
    m2x: float | None = None
    m2y: float | None = None
    m2z: float | None = None
    m3x: float | None = None
    m3y: float | None = None
    m3z: float | None = None

    qx: float | None = None
    qy: float | None = None
    qz: float | None = None
    qw: float | None = None