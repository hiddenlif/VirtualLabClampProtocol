"""Public scientific model for the disclosed clamp-protocol instance.

The release copies this module into the public environment and independently
into the verifier.  It evaluates submitted JSON data only; it never imports
submitted code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import expm

PARAMETER_NAMES = (
    "activation_rate_scale",
    "deactivation_rate_scale",
    "inactivation_rate_scale",
    "recovery_rate_scale",
    "conductance_scale",
)


def load_json(path: str | Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _strict_number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def validate_protocol(data: dict, protocol: dict) -> list[tuple[float, float]]:
    if not isinstance(protocol, dict) or set(protocol) != {"segments"}:
        raise ValueError("protocol must contain exactly the key 'segments'")
    raw = protocol["segments"]
    count = int(data["protocol_constraints"]["segment_count"])
    if not isinstance(raw, list) or len(raw) != count:
        raise ValueError(f"segments must be a list of length {count}")

    voltage_grid = {float(v) for v in data["protocol_constraints"]["voltage_grid_mv"]}
    duration_grid = {float(v) for v in data["protocol_constraints"]["duration_grid_ms"]}
    segments: list[tuple[float, float]] = []
    for index, segment in enumerate(raw):
        if not isinstance(segment, dict) or set(segment) != {
            "voltage_mv",
            "duration_ms",
        }:
            raise ValueError(f"segment {index} has the wrong keys")
        voltage = _strict_number(segment["voltage_mv"], f"segment {index} voltage_mv")
        duration = _strict_number(
            segment["duration_ms"], f"segment {index} duration_ms"
        )
        if voltage not in voltage_grid:
            raise ValueError(f"segment {index} voltage is off-grid")
        if duration not in duration_grid:
            raise ValueError(f"segment {index} duration is off-grid")
        if segments and voltage == segments[-1][0]:
            raise ValueError("adjacent segments may not repeat the same voltage")
        segments.append((voltage, duration))

    expected_time = float(data["protocol_constraints"]["total_duration_ms"])
    if abs(sum(duration for _, duration in segments) - expected_time) > 1e-9:
        raise ValueError(f"total duration must be {expected_time:g} ms")
    terminal = data["protocol_constraints"]["terminal_hold"]
    if segments[-1][0] != float(terminal["voltage_mv"]):
        raise ValueError("last segment must be the terminal holding voltage")
    if segments[-1][1] < float(terminal["minimum_duration_ms"]):
        raise ValueError("terminal holding segment is too short")
    if not any(voltage >= 0.0 for voltage, _ in segments[:-1]):
        raise ValueError("protocol must contain a nonnegative activation segment")
    if not any(voltage <= -80.0 for voltage, _ in segments[:-1]):
        raise ValueError("protocol must contain a recovery segment at or below -80 mV")
    if not any(-60.0 <= voltage <= -20.0 for voltage, _ in segments[:-1]):
        raise ValueError("protocol must contain a mid-voltage kinetic segment")
    return segments


def _rates(
    voltage_mv: float, variant: dict, log_scales: np.ndarray
) -> tuple[float, ...]:
    scale = np.exp(log_scales[:4])
    shift = float(variant["voltage_shift_mv"])
    voltage = voltage_mv - shift
    multipliers = variant["rate_multipliers"]
    alpha = (
        0.010
        * math.exp((voltage + 45.0) / 38.0)
        * float(multipliers["activation"])
        * scale[0]
    )
    beta = (
        0.028
        * math.exp(-(voltage + 45.0) / 44.0)
        * float(multipliers["deactivation"])
        * scale[1]
    )
    inactivation = (
        0.020
        / (1.0 + math.exp(-(voltage + 18.0) / 13.0))
        * float(multipliers["inactivation"])
        * scale[2]
    )
    recovery = (
        0.010
        / (1.0 + math.exp((voltage + 58.0) / 11.0))
        * float(multipliers["recovery"])
        * scale[3]
    )
    return alpha, beta, inactivation, recovery


def _generator(voltage_mv: float, variant: dict, log_scales: np.ndarray) -> np.ndarray:
    """Column-vector generator for closed, open, inactivated probabilities."""
    alpha, beta, inactivation, recovery = _rates(voltage_mv, variant, log_scales)
    return np.array(
        [
            [-alpha, beta, recovery],
            [alpha, -(beta + inactivation), 0.0],
            [0.0, inactivation, -recovery],
        ],
        dtype=float,
    )


def _equilibrium(
    voltage_mv: float, variant: dict, log_scales: np.ndarray
) -> np.ndarray:
    q = _generator(voltage_mv, variant, log_scales)
    system = q.copy()
    system[-1, :] = 1.0
    rhs = np.array([0.0, 0.0, 1.0])
    state = np.linalg.solve(system, rhs)
    state[state < 0.0] = 0.0
    return state / state.sum()


def simulate_currents(
    data: dict,
    segments: list[tuple[float, float]],
    variant: dict,
    log_scales: np.ndarray,
) -> np.ndarray:
    sample_interval = float(data["apparatus"]["sample_interval_ms"])
    state = _equilibrium(
        float(data["apparatus"]["initial_hold_mv"]), variant, log_scales
    )
    currents: list[float] = []
    conductance = float(variant["conductance_ns"]) * math.exp(float(log_scales[4]))
    reversal = float(data["apparatus"]["reversal_potential_mv"])
    for voltage, duration in segments:
        steps = round(duration / sample_interval)
        if abs(steps * sample_interval - duration) > 1e-9 or steps < 1:
            raise ValueError("duration is incompatible with the sample interval")
        transition = expm(_generator(voltage, variant, log_scales) * sample_interval)
        for _ in range(steps):
            state = transition @ state
            state = np.maximum(state, 0.0)
            state /= state.sum()
            currents.append(conductance * state[1] * (voltage - reversal))
    return np.asarray(currents, dtype=float)


def _variant_metrics(
    data: dict, segments: list[tuple[float, float]], variant: dict
) -> dict:
    delta = float(data["information_model"]["finite_difference_log_step"])
    nominal = simulate_currents(data, segments, variant, np.zeros(5))
    columns = []
    for index in range(5):
        plus = np.zeros(5)
        minus = np.zeros(5)
        plus[index] = delta
        minus[index] = -delta
        columns.append(
            (
                simulate_currents(data, segments, variant, plus)
                - simulate_currents(data, segments, variant, minus)
            )
            / (2.0 * delta)
        )
    jacobian = np.column_stack(columns)
    noise = data["apparatus"]["noise_model"]
    sigma = np.sqrt(
        float(noise["baseline_pA"]) ** 2
        + float(noise["current_factor_pA"]) * np.abs(nominal)
    )
    weighted = jacobian / sigma[:, None]
    fisher = weighted.T @ weighted
    eigenvalues = np.linalg.eigvalsh(fisher)
    positive_floor = float(data["information_model"]["reporting_eigenvalue_floor"])
    log_determinant = float(np.log(np.maximum(eigenvalues, positive_floor)).sum())

    five_sigma = float(data["apparatus"]["saturation_sigma_multiplier"])
    amplifier_limit = float(data["apparatus"]["amplifier_limit_pa"])
    excursions = np.abs(nominal) + five_sigma * sigma
    saturation_count = int(np.count_nonzero(excursions > amplifier_limit + 1e-12))
    return {
        "variant_id": variant["id"],
        "log_determinant": log_determinant,
        "minimum_eigenvalue": float(eigenvalues[0]),
        "maximum_five_sigma_current_pa": float(excursions.max()),
        "saturation_sample_count": saturation_count,
        "terminal_open_probability": float(_terminal_state(data, segments, variant)[1]),
    }


def _terminal_state(
    data: dict, segments: list[tuple[float, float]], variant: dict
) -> np.ndarray:
    state = _equilibrium(
        float(data["apparatus"]["initial_hold_mv"]), variant, np.zeros(5)
    )
    float(data["apparatus"]["sample_interval_ms"])
    for voltage, duration in segments:
        state = expm(_generator(voltage, variant, np.zeros(5)) * duration) @ state
    state = np.maximum(state, 0.0)
    return state / state.sum()


def evaluate(data: dict, protocol: dict) -> dict:
    segments = validate_protocol(data, protocol)
    per_variant = [
        _variant_metrics(data, segments, variant) for variant in data["cell_variants"]
    ]
    weights = np.asarray(
        [float(v["design_weight"]) for v in data["cell_variants"]], dtype=float
    )
    logdets = np.asarray([v["log_determinant"] for v in per_variant])
    eigmins = np.asarray([v["minimum_eigenvalue"] for v in per_variant])
    return {
        "protocol_legal": True,
        "minimum_log_determinant": float(logdets.min()),
        "minimum_eigenvalue": float(eigmins.min()),
        "weighted_mean_log_determinant": float(
            np.dot(weights, logdets) / weights.sum()
        ),
        "saturation_sample_count": int(
            sum(v["saturation_sample_count"] for v in per_variant)
        ),
        "maximum_five_sigma_current_pa": float(
            max(v["maximum_five_sigma_current_pa"] for v in per_variant)
        ),
        "maximum_terminal_open_probability": float(
            max(v["terminal_open_probability"] for v in per_variant)
        ),
        "variant_metrics": per_variant,
    }


def objective(data: dict, protocol: dict) -> float:
    try:
        metrics = evaluate(data, protocol)
    except Exception:
        return -1.0e12
    penalty = 0.0
    penalty += 1000.0 * metrics["saturation_sample_count"]
    terminal_limit = float(
        data["protocol_constraints"]["maximum_terminal_open_probability"]
    )
    if metrics["maximum_terminal_open_probability"] > terminal_limit:
        penalty += 100000.0 * (
            metrics["maximum_terminal_open_probability"] - terminal_limit
        )
    return (
        metrics["minimum_log_determinant"]
        + 2.0 * math.log(max(metrics["minimum_eigenvalue"], 1e-16))
        + 0.15 * metrics["weighted_mean_log_determinant"]
        - penalty
    )
