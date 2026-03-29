"""Abstract lantern model interface for future high-fidelity backends."""

from __future__ import annotations

import numpy as np


class BaseLanternModel:
    """Common interface for lantern throughput and power propagation models."""

    def eta_internal(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return internal throughput on the wavelength grid."""
        raise NotImplementedError

    def propagate_power(self, p_in: np.ndarray, lam_nm: np.ndarray | float) -> dict:
        """Propagate modal power to the output ports at a given wavelength."""
        raise NotImplementedError
