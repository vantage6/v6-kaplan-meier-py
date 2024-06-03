from enum import Enum


class NoiseType(str, Enum):
    NONE = "NONE"
    GAUSSIAN = "GAUSSIAN"
    POISSON = "POISSON"
