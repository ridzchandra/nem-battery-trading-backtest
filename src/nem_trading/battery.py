from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Battery:
    capacity_mwh: float = 100.0
    max_power_mw: float = 50.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    state_of_charge_mwh: float = 50.0

    def _max_interval_energy(self, interval_minutes: int) -> float:
        return self.max_power_mw * interval_minutes / 60.0

    def charge(self, price: float, interval_minutes: int = 5) -> tuple[float, float]:
        """Charge the battery and return (grid_mwh_bought, cashflow)."""
        max_grid_mwh = self._max_interval_energy(interval_minutes)
        available_storage = self.capacity_mwh - self.state_of_charge_mwh
        grid_mwh = min(max_grid_mwh, available_storage / self.charge_efficiency)
        self.state_of_charge_mwh += grid_mwh * self.charge_efficiency
        cashflow = -grid_mwh * price
        return grid_mwh, cashflow

    def discharge(self, price: float, interval_minutes: int = 5) -> tuple[float, float]:
        """Discharge the battery and return (grid_mwh_sold, cashflow)."""
        max_grid_mwh = self._max_interval_energy(interval_minutes)
        available_grid_mwh = self.state_of_charge_mwh * self.discharge_efficiency
        grid_mwh = min(max_grid_mwh, available_grid_mwh)
        self.state_of_charge_mwh -= grid_mwh / self.discharge_efficiency
        cashflow = grid_mwh * price
        return grid_mwh, cashflow
