# %%
from dataclasses import dataclass
from math import exp



@dataclass(frozen=True)
class CropParameters:
    # Species parameters.
    T_base: float
    T_opt: float
    RUE: float
    I_50maxH: float
    I_50maxW: float
    T_heat: float  # T_max in Table 1a.
    T_ext: float
    S_CO2: float
    S_water: float

    # Cultivar parameters.
    T_sum: float
    HI: float
    I_50A: float
    I_50B: float

    def fSolar(self, TT, I_50A: float, I_50B: float, fSolar_max: float = 0.95):
        return min(
            fSolar_max / (1 + exp(-0.01 * (TT - I_50A))),
            fSolar_max / (1 + exp(0.01 * (TT - (self.T_sum - I_50B)))),
        )

    def fTemp(self, T_mean):
        if T_mean < self.T_base:
            return 0
        elif self.T_base <= T_mean < self.T_opt:
            return (T_mean - self.T_base) / (self.T_opt - self.T_base)
        elif T_mean >= self.T_opt:
            return 1

    def fHeat(self, T_max: float):
        if T_max <= self.T_heat:
            return 1
        elif self.T_heat < T_max <= self.T_ext:
            return 1 - (T_max - self.T_heat) / (self.T_ext - self.T_heat)
        elif T_max > self.T_ext:
            return 0

    def fCO2(self, CO2):
        if 350 <= CO2 <= 700:
            return 1 + self.S_CO2 * (CO2 - 350)
        elif CO2 > 700:
            return 1 + self.S_CO2 * 350

    def fWater(self, ARID):
        assert 0 <= ARID <= 1
        return 1 - self.S_water * ARID


@dataclass
class Crop:
    parameters: CropParameters
    i: int = 0
    TT: float = 0
    I_50A: float = float("nan")
    I_50B: float = float("nan")
    biomass: float = 0  # Kg (per m^2?)

    def __post_init__(self):
        self.I_50A = self.parameters.I_50A
        self.I_50B = self.parameters.I_50B

    def next_day(self, *, radiation, T_mean, T_max, CO2, ARID):
        """
        radiation in MJ/m^2,
        T_mean and T_max in degrees C,
        CO2 in ppm,
        ARID is water shortage in [0, 1].
        """

        p = self.parameters

        self.biomass += (
            radiation
            * p.fSolar(self.TT, self.I_50A, self.I_50B)
            * p.RUE
            * p.fCO2(CO2)
            * p.fTemp(T_mean)
            * min(p.fHeat(T_max), p.fWater(ARID))
        )

        self.i += 1
        self.TT += max(0, T_mean - p.T_base)
        self.I_50B += p.I_50maxH * (1 - p.fHeat(T_max))
        self.I_50B += p.I_50maxW * (1 - p.fWater(ARID))

    def yields(self):
        return self.biomass * self.parameters.HI


# %%