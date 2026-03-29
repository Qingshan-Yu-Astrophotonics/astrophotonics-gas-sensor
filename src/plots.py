"""Matplotlib plotting utilities for simulation outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


FIG_DPI = 180


def _finalize(fig: plt.Figure, output_path: str | Path) -> None:
    """Apply layout and save the figure."""
    fig.tight_layout()
    fig.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


def plot_mode_count(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot multimode-port mode count versus wavelength."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for result in scenario_results:
        ax.plot(result["lam_nm"], result["mode_count"], linewidth=2, label=f'{result["n_port"]} ports')
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Supported mode count")
    ax.set_title("Photonic Lantern Mode Count")
    ax.grid(alpha=0.25)
    ax.legend()
    _finalize(fig, output_path)


def plot_eta_internal(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot internal lantern throughput versus wavelength."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for result in scenario_results:
        ax.plot(result["lam_nm"], result["eta_internal"], linewidth=2, label=f'{result["n_port"]} ports')
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Internal throughput")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Internal Lantern Throughput")
    ax.grid(alpha=0.25)
    ax.legend()
    _finalize(fig, output_path)


def plot_eta_sys(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot full system throughput versus wavelength."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for result in scenario_results:
        ax.plot(result["lam_nm"], result["eta_sys"], linewidth=2, label=f'{result["n_port"]} ports')
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("System throughput")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("End-to-End System Throughput")
    ax.grid(alpha=0.25)
    ax.legend()
    _finalize(fig, output_path)


def plot_snr_vs_mag(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot SNR versus AB magnitude for each port-count scenario."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for result in scenario_results:
        ax.plot(result["m_ab_grid"], result["snr_grid"], linewidth=2, label=f'{result["n_port"]} ports')
    ax.set_xlabel("AB magnitude")
    ax.set_ylabel("SNR")
    ax.set_yscale("log")
    ax.set_title("SNR vs. AB Magnitude")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    _finalize(fig, output_path)


def plot_mlim_vs_time(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot limiting magnitude versus total integration time."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for result in scenario_results:
        times = np.array([row["t_total_s"] for row in result["m_lim_vs_time"]], dtype=float)
        m_lim = np.array([row["m_lim"] for row in result["m_lim_vs_time"]], dtype=float)
        ax.plot(times, m_lim, marker="o", linewidth=2, label=f'{result["n_port"]} ports')
    ax.set_xscale("log")
    ax.set_xlabel("Total integration time [s]")
    ax.set_ylabel("Limiting magnitude")
    ax.set_title("Limiting Magnitude vs. Total Integration Time")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    _finalize(fig, output_path)


def plot_port_power_distribution(scenario_results: list[dict], output_path: str | Path) -> None:
    """Plot example output-port power distributions at the reference wavelength."""
    n_scenario = len(scenario_results)
    fig, axes = plt.subplots(1, n_scenario, figsize=(4.5 * n_scenario, 4), squeeze=False)
    for ax, result in zip(axes[0], scenario_results):
        p_out = np.asarray(result["port_payload"]["p_out"], dtype=float)
        ax.bar(np.arange(1, p_out.size + 1), p_out, color="#1f77b4")
        ax.set_xlabel("Port index")
        ax.set_ylabel("Output power fraction")
        ax.set_title(f'{result["n_port"]} ports @ {result["port_payload"]["lam_nm"]:.0f} nm')
        ax.set_ylim(0.0, max(0.05, 1.1 * p_out.max()))
        ax.grid(alpha=0.25, axis="y")
    _finalize(fig, output_path)
