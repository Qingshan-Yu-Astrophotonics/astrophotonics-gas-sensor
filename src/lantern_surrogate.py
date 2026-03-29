"""Photonic lantern internal surrogate throughput model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lantern_repo_interface import BaseLanternModel
from .utils import as_numpy_1d, ensure_positive, validate_probability_like


@dataclass(frozen=True)
class LanternInternalModel(BaseLanternModel):
    """Fast surrogate model for lantern internal throughput and port allocation."""

    n_port: int
    lambda0_nm: float
    alpha_ad: float
    eta0: float
    sigma_mix: float
    w_cut: float
    input_profile: str = "uniform"
    port_map_mode: str = "uniform"
    random_seed: int = 12345

    def __post_init__(self) -> None:
        if self.n_port <= 0:
            raise ValueError("n_port must be a positive integer.")
        ensure_positive("lambda0_nm", float(self.lambda0_nm))
        ensure_positive("w_cut", float(self.w_cut))
        if self.alpha_ad < 0.0:
            raise ValueError("alpha_ad must be >= 0.")
        if self.sigma_mix < 0.0:
            raise ValueError("sigma_mix must be >= 0.")
        validate_probability_like("eta0", float(self.eta0))

    def mm_mode_count(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return the surrogate multimode-port supported mode count."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        return self.n_port * (self.lambda0_nm / lam_nm) ** 2

    def _effective_mode_count(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return an integer-like mode count used for loss estimation."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        return np.maximum(self.n_port, np.ceil(self.mm_mode_count(lam_nm)))

    def eta_match(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return the mode-count matching throughput."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        effective_modes = self._effective_mode_count(lam_nm)
        return np.minimum(1.0, self.n_port / effective_modes)

    def eta_ad(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return the surrogate adiabatic taper throughput."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        excess_mode_ratio = np.maximum(0.0, self._effective_mode_count(lam_nm) / self.n_port - 1.0)
        return np.exp(-self.alpha_ad * excess_mode_ratio)

    def eta_par(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return wavelength-independent parasitic throughput."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        return np.full_like(lam_nm, self.eta0, dtype=float)

    def eta_internal(self, lam_nm: np.ndarray | float) -> np.ndarray:
        """Return the total surrogate internal throughput."""
        lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
        eta = self.eta_par(lam_nm) * self.eta_match(lam_nm) * self.eta_ad(lam_nm)
        return np.clip(eta, 0.0, 1.0)

    def generate_input_modes(self, n_mode_in: int, profile: str | None = None) -> np.ndarray:
        """Generate a normalized non-negative input modal power vector."""
        if n_mode_in <= 0:
            raise ValueError("n_mode_in must be positive.")
        active_profile = profile or self.input_profile
        if active_profile == "uniform":
            p_in = np.ones(n_mode_in, dtype=float)
        elif active_profile == "exponential":
            indices = np.arange(n_mode_in, dtype=float)
            decay_scale = max(1.0, n_mode_in / 4.0)
            p_in = np.exp(-indices / decay_scale)
        else:
            raise ValueError(f"Unsupported input profile: {active_profile}.")
        return p_in / p_in.sum()

    def soft_match_mask(self, n_mode_in: int) -> np.ndarray:
        """Return the soft cutoff mask applied before modal mixing."""
        if n_mode_in <= 0:
            raise ValueError("n_mode_in must be positive.")
        indices = np.arange(1, n_mode_in + 1, dtype=float)
        mask = 1.0 / (1.0 + np.exp((indices - self.n_port) / self.w_cut))
        return np.clip(mask, 0.0, 1.0)

    def mixing_matrix(self, n_mode: int) -> np.ndarray:
        """Construct a column-normalized Gaussian-kernel mixing matrix."""
        if n_mode <= 0:
            raise ValueError("n_mode must be positive.")
        if self.sigma_mix == 0.0:
            return np.eye(n_mode, dtype=float)
        indices = np.arange(n_mode, dtype=float)
        delta = indices[:, None] - indices[None, :]
        kernel = np.exp(-(delta**2) / (2.0 * self.sigma_mix**2))
        return kernel / kernel.sum(axis=0, keepdims=True)

    def port_map(self, n_mode: int, mode: str | None = None) -> np.ndarray:
        """Return the port mapping matrix from mixed modes to output ports."""
        if n_mode <= 0:
            raise ValueError("n_mode must be positive.")
        active_mode = mode or self.port_map_mode
        if active_mode == "uniform":
            mapping = np.full((self.n_port, n_mode), 1.0 / self.n_port, dtype=float)
        elif active_mode == "random_fixed":
            rng = np.random.default_rng(self.random_seed)
            mapping = rng.random((self.n_port, n_mode))
            mapping /= mapping.sum(axis=0, keepdims=True)
        else:
            raise ValueError(f"Unsupported port map mode: {active_mode}.")
        return mapping

    def propagate_power(self, p_in: np.ndarray, lam_nm: np.ndarray | float) -> dict:
        """Propagate modal power to output ports at one wavelength sample."""
        p_in = as_numpy_1d(p_in, name="p_in")
        if np.any(p_in < 0.0):
            raise ValueError("p_in must be non-negative.")
        total_in = p_in.sum()
        if total_in <= 0.0:
            raise ValueError("p_in must contain positive total power.")

        lam_arr = as_numpy_1d(lam_nm, name="lam_nm")
        if lam_arr.size != 1:
            raise ValueError("propagate_power expects a single wavelength sample.")
        lam_scalar_nm = float(lam_arr[0])

        p_norm = p_in / total_in
        mask = self.soft_match_mask(p_norm.size)
        mixed = self.mixing_matrix(p_norm.size) @ (mask * p_norm)
        remapped = self.port_map(p_norm.size) @ mixed
        eta_internal = float(self.eta_internal(np.array([lam_scalar_nm]))[0])
        p_out = eta_internal * remapped

        return {
            "lam_nm": lam_scalar_nm,
            "p_in": p_norm,
            "mask": mask,
            "mixed": mixed,
            "p_out": p_out,
            "eta_internal": eta_internal,
            "surviving_pre_internal": float(remapped.sum()),
        }
