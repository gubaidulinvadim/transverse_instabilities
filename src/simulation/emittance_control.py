"""Configure vertical-emittance control for single-bunch tracking."""

from collections.abc import Mapping

import numpy as np
from mbtrack2.tracking import SkewQuadrupole


EMITTANCE_CONTROL_METHODS = {
    "auto",
    "white_noise",
    "skew_quadrupole",
    "ac_skew_quadrupole",
}


def _finite_number(
    config: Mapping[str, object],
    name: str,
    default: float,
    *,
    minimum: float | None = None,
) -> float:
    value = config.get(name, default)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return float(value)


def _method_from_config(
    config: Mapping[str, object],
    emittance_ratio: float,
) -> str:
    method = config.get("emittance_control_method")
    if method is None or method == "auto":
        return "skew_quadrupole" if emittance_ratio == 1.0 else "white_noise"
    if not isinstance(method, str) or method not in EMITTANCE_CONTROL_METHODS:
        supported = ", ".join(sorted(EMITTANCE_CONTROL_METHODS))
        raise ValueError(
            f"Unsupported emittance_control_method. Use one of: {supported}."
        )
    return method


def _nearest_difference_resonance_frequency(tune: np.ndarray) -> float:
    tune_difference = float(tune[0] - tune[1])
    return abs(tune_difference - round(tune_difference))


def setup_emittance_control(
    ring,
    config: Mapping[str, object],
):
    """Set ring emittance/tunes and return the selected method and element."""
    emittance_ratio = _finite_number(
        config,
        "emittance_ratio",
        0.3,
        minimum=0.0,
    )
    method = _method_from_config(config, emittance_ratio)

    if method == "white_noise":
        ring.emit[1] = emittance_ratio * ring.emit[0]
        return method, None

    base_emittance_ratio = _finite_number(
        config,
        "coupling_base_emittance_ratio",
        0.02,
        minimum=0.0,
    )
    ring.emit[1] = base_emittance_ratio * ring.emit[0]

    if method == "skew_quadrupole":
        ring.tune[0] = _finite_number(config, "skew_tune_x", 54.2)
        ring.tune[1] = _finite_number(config, "skew_tune_y", 18.2)
        strength = _finite_number(config, "skew_strength", 0.001)
        return method, SkewQuadrupole(strength=strength)

    try:
        from mbtrack2.tracking import ACSkewQuadrupole
    except ImportError as exc:
        raise ImportError(
            "The ac_skew_quadrupole method requires an mbtrack2 version "
            "that provides ACSkewQuadrupole."
        ) from exc

    strength = _finite_number(config, "ac_skew_strength", 0.001)
    default_frequency = _nearest_difference_resonance_frequency(ring.tune)
    frequency = _finite_number(
        config,
        "ac_skew_frequency",
        default_frequency,
        minimum=0.0,
    )
    seed = config.get("ac_skew_seed", 42)
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("ac_skew_seed must be a non-negative integer.")

    element = ACSkewQuadrupole(
        strength=strength,
        frequency=frequency,
        phase=0.0,
        frequency_jitter=0.0,
        rng=np.random.default_rng(seed),
    )
    return method, element
