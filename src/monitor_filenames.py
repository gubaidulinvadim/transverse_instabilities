"""Generate monitor filenames from tracking configuration."""

from collections.abc import Mapping
from os import PathLike, fspath
from pathlib import Path

try:
    from .config import load_toml_config
    from .simulation.fill_patterns import build_filling_pattern
except ImportError:
    from config import load_toml_config
    from simulation.fill_patterns import build_filling_pattern


ConfigSource = Mapping[str, object] | str | PathLike[str]


def _script_config(config_source: ConfigSource) -> Mapping[str, object]:
    if isinstance(config_source, Mapping):
        config = config_source
    else:
        config = load_toml_config(fspath(config_source))

    script_config = config.get("script")
    if script_config is None:
        return config
    if not isinstance(script_config, Mapping):
        raise ValueError("The 'script' configuration section must be a table.")
    return script_config


def _wake_types_string(config: Mapping[str, object]) -> str:
    wake_types = config.get("wake_types", ["Wydip"])
    return "-".join(
        str(value).replace("'", "").replace('"', "")
        for value in wake_types
    )


def _emittance_control_method(config: Mapping[str, object]) -> str:
    emittance_ratio = config.get("emittance_ratio", 0.3)
    method = config.get("emittance_control_method")
    if method is None or method == "auto":
        return "skew_quadrupole" if emittance_ratio == 1.0 else "white_noise"
    if method not in {
        "white_noise",
        "skew_quadrupole",
        "ac_skew_quadrupole",
    }:
        raise ValueError(f"Unsupported emittance_control_method: {method}.")
    return str(method)


def _single_bunch_filename(config: Mapping[str, object]) -> str:
    folder = config["folder"]
    n_turns = config.get("n_turns", 100_000)
    n_macroparticles = config.get("n_macroparticles", 100_000)
    n_bin = config.get("n_bin", 100)
    bunch_current = config.get("bunch_current", 1e-3)
    qp_x = config.get("Qp_x", 1.6)
    qp_y = config.get("Qp_y", 1.6)
    id_state = config.get("id_state", "open")
    include_zlong = config.get("include_Zlong", False)
    harmonic_cavity = config.get("harmonic_cavity", False)
    feedback_tau = config.get("feedback_tau", 0)
    feedback_phase = config.get("feedback_phase", -90)
    sc = config.get("sc", False)
    ibs = config.get("ibs", False)
    emittance_ratio = config.get("emittance_ratio", 0.3)
    method = _emittance_control_method(config)

    if method == "white_noise":
        control_details = ""
    elif method == "skew_quadrupole":
        control_details = (
            f",base_er={config.get('coupling_base_emittance_ratio', 0.02):.3f}"
            f",skew_k={config.get('skew_strength', 0.001):.2e}"
            f",skew_qx={config.get('skew_tune_x', 54.2):.3f}"
            f",skew_qy={config.get('skew_tune_y', 18.2):.3f}"
        )
    else:
        control_details = (
            f",base_er={config.get('coupling_base_emittance_ratio', 0.02):.3f}"
            f",ac_k={config.get('ac_skew_strength', 0.001):.2e}"
            f",ac_f={config.get('ac_skew_frequency', 0.02):.4f}"
        )

    return (
        f"{folder}mon(nmp={n_macroparticles:.1e},"
        f"nt={n_turns:.1e},"
        f"nb={n_bin},"
        f"I={bunch_current:.2e},"
        f"Qpx={qp_x:.2f},"
        f"Qpy={qp_y:.2f},"
        f"id={id_state},"
        f"Zl={include_zlong},"
        f"HC={harmonic_cavity},"
        f"fb_tau={feedback_tau:.1e},"
        f"phi={feedback_phase:g},"
        f"sc={sc},"
        f"ibs={ibs},"
        f"wakes={_wake_types_string(config)},"
        f"emit_ctrl={method},"
        f"er={emittance_ratio}"
        f"{control_details})"
    )


def _multi_bunch_filename(
    config: Mapping[str, object],
    harmonic_number: int,
) -> str:
    folder = config["folder"]
    n_turns = config.get("n_turns", 75_000)
    n_macroparticles = config.get("n_macroparticles", 100_000)
    n_bin = config.get("n_bin", 100)
    bunch_current = config.get("bunch_current", 1.2e-3)
    qp_x = config.get("Qp_x", 1.8)
    qp_y = config.get("Qp_y", 1.4)
    id_state = config.get("id_state", "open")
    include_zlong = config.get("include_Zlong", False)
    harmonic_cavity = config.get("harmonic_cavity", False)
    feedback_tau = config.get("feedback_tau", 100)
    feedback_phase = config.get("feedback_phase", -90)
    sc = config.get("sc", False)
    ibs = config.get("ibs", False)
    fill_pattern_name = config.get("fill_pattern", "full")
    filling_pattern = build_filling_pattern(
        harmonic_number,
        bunch_current,
        config,
    )
    n_bunches = int((filling_pattern != 0).sum())

    return (
        f"{folder}monitors(n_mp={n_macroparticles:.1e}"
        f",n_turns={n_turns:.1e}"
        f",n_bin={n_bin}"
        f",bunch_current={bunch_current:.1e}"
        f",n_bunches={n_bunches}"
        f",fill_pattern={fill_pattern_name}"
        f",Qp_x={qp_x:.2f}"
        f",Qp_y={qp_y:.2f}"
        f",ID_state={id_state}"
        f",include_Zlong={include_zlong}"
        f",harmonic_cavity={harmonic_cavity}"
        f",feedback_tau={feedback_tau:.1e}"
        f",phi={feedback_phase:g}"
        f",sc={sc}"
        f",ibs={ibs}"
        f",wake_types={_wake_types_string(config)})"
    )


def get_monitor_filename(
    config_source: ConfigSource,
    tracking_script: str | None = None,
    *,
    harmonic_number: int = 416,
    include_extension: bool = False,
) -> str:
    """Return the monitor filename generated by a tracking script.

    ``config_source`` can be a parsed configuration mapping or a TOML file
    path. Full jobsmith configurations with a ``[script]`` section and flat
    script configurations are both supported. The returned name matches the
    value passed to the mbtrack2 monitor; use ``include_extension=True`` to
    obtain the generated HDF5 file path for postprocessing.
    """
    config = _script_config(config_source)
    configured_script = tracking_script or config.get("name")
    if not isinstance(configured_script, str):
        raise ValueError(
            "tracking_script is required when the configuration has no "
            "'name' entry."
        )

    script_name = Path(configured_script).name
    if script_name == "track_TI.py":
        filename = _single_bunch_filename(config)
    elif script_name == "track_mb.py":
        filename = _multi_bunch_filename(config, harmonic_number)
    else:
        raise ValueError(
            "Monitor filename generation supports track_TI.py and track_mb.py; "
            f"got {script_name!r}."
        )

    if include_extension:
        return f"{filename}.hdf5"
    return filename
