"""CLI entrypoint for the astrophotonics lantern surrogate simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config_loader import load_config_bundle
from src.plots import (
    plot_eta_internal,
    plot_eta_sys,
    plot_mlim_vs_time,
    plot_mode_count,
    plot_port_power_distribution,
    plot_snr_vs_mag,
)
from src.sweep import run_sweep
from src.utils import ensure_dir


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the photonic lantern surrogate simulation.")
    parser.add_argument("--config-dir", default="config", help="Directory containing YAML config files.")
    return parser.parse_args()


def main() -> None:
    """Run the full simulation sweep and save figures and tables."""
    args = parse_args()
    config_bundle = load_config_bundle(args.config_dir)
    outputs_cfg = config_bundle["base"]["outputs"]
    figures_dir = ensure_dir(outputs_cfg["figures_dir"])
    tables_dir = ensure_dir(outputs_cfg["tables_dir"])

    sweep_results = run_sweep(config_bundle)
    scenario_results = sweep_results["scenario_results"]

    sweep_results["eta_internal_summary"].to_csv(tables_dir / "eta_internal_summary.csv", index=False)
    sweep_results["eta_sys_summary"].to_csv(tables_dir / "eta_sys_summary.csv", index=False)
    sweep_results["limiting_magnitude_summary"].to_csv(tables_dir / "limiting_magnitude_summary.csv", index=False)

    plot_mode_count(scenario_results, figures_dir / "mode_count_vs_lambda.png")
    plot_eta_internal(scenario_results, figures_dir / "eta_internal_vs_lambda.png")
    plot_eta_sys(scenario_results, figures_dir / "eta_sys_vs_lambda.png")
    plot_snr_vs_mag(scenario_results, figures_dir / "snr_vs_mag.png")
    plot_mlim_vs_time(scenario_results, figures_dir / "m_lim_vs_time.png")
    plot_port_power_distribution(scenario_results, figures_dir / "port_power_distribution_example.png")

    for result in scenario_results:
        print(f'[INFO] Running scenario: {result["name"]}')
        print(f'[INFO] Band-averaged eta_internal = {result["eta_internal_bandavg"]:.4f}')
        print(f'[INFO] Band-averaged eta_sys = {result["eta_sys_bandavg"]:.4f}')
        print(f'[INFO] m_lim (SNR={config_bundle["base"]["snr_target"]:.1f}, t={config_bundle["base"]["observation"]["target_total_time_s"]:.0f} s) = {result["m_lim_target"]:.3f}')

    print(f'[INFO] Figures saved to: {Path(figures_dir).resolve()}')
    print(f'[INFO] Tables saved to: {Path(tables_dir).resolve()}')


if __name__ == "__main__":
    main()
