"""System-level throughput assembly for telescope, lantern, and detector."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .detector import DetectorConfig, build_detector_config
from .lantern_repo_interface import BaseLanternModel
from .telescope import effective_collecting_area, mirror_train_throughput
from .utils import broadcast_to_grid


@dataclass
class SystemModel:
    """Assemble system throughput curves and telescope area from config inputs."""

    telescope_cfg: dict
    detector_cfg_raw: dict
    lantern_model: BaseLanternModel
    detector: DetectorConfig = field(init=False)

    def __post_init__(self) -> None:
        self.detector = build_detector_config(self.detector_cfg_raw)

    def effective_area_m2(self) -> float:
        """Return the telescope effective collecting area in square meters."""
        return effective_collecting_area(
            D_m=float(self.telescope_cfg["D_m"]),
            D_obs_m=float(self.telescope_cfg["D_obs_m"]),
        )

    def eta_atm(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return atmospheric throughput on the wavelength grid."""
        return broadcast_to_grid(self.telescope_cfg["eta_atm"], lam_nm, name="eta_atm")

    def eta_tel(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return mirror-train throughput on the wavelength grid."""
        throughput = mirror_train_throughput(
            reflectivity=float(self.telescope_cfg["mirror_reflectivity"]),
            n_mirrors=int(self.telescope_cfg["n_mirrors"]),
        )
        return np.full_like(lam_nm, throughput, dtype=float)

    def eta_fore(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return fore-optics throughput on the wavelength grid."""
        return broadcast_to_grid(self.telescope_cfg["eta_fore"], lam_nm, name="eta_fore")

    def eta_inj(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return injection efficiency on the wavelength grid."""
        return broadcast_to_grid(self.telescope_cfg["eta_inj"], lam_nm, name="eta_inj")

    def qe(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return detector quantum efficiency on the wavelength grid."""
        return self.detector.qe_curve(lam_nm)

    def component_curves(self, lam_nm: np.ndarray) -> dict[str, np.ndarray]:
        """Return all throughput components and the combined system throughput."""
        eta_internal = self.lantern_model.eta_internal(lam_nm)
        components = {
            "eta_atm": self.eta_atm(lam_nm),
            "eta_tel": self.eta_tel(lam_nm),
            "eta_fore": self.eta_fore(lam_nm),
            "eta_inj": self.eta_inj(lam_nm),
            "eta_internal": eta_internal,
            "qe": self.qe(lam_nm),
        }
        components["eta_sys"] = (
            components["eta_atm"]
            * components["eta_tel"]
            * components["eta_fore"]
            * components["eta_inj"]
            * components["eta_internal"]
            * components["qe"]
        )
        return components

    def eta_sys(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return the total system throughput on the wavelength grid."""
        return self.component_curves(lam_nm)["eta_sys"]
