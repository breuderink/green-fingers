# %%
from dataclasses import dataclass
from math import exp

import pandas as pd
import plotly.express as px


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


wheat_yecora_rojo = CropParameters(
    T_sum=2200,
    HI=0.36,
    I_50A=480,
    I_50B=200,
    T_base=0,
    T_opt=15,
    RUE=1.24,
    I_50maxH=100,
    I_50maxW=25,
    T_heat=34,
    T_ext=45,
    S_CO2=0.08,
    S_water=0.04,
)


@dataclass
class Crop:
    parameters: CropParameters
    i: int = 0
    TT: float = 0
    I_50A: float = float("nan")
    I_50B: float = float("nan")
    biomass: float = 0

    def __post_init__(self):
        self.I_50A = self.parameters.I_50A
        self.I_50B = self.parameters.I_50B

    def next_day(self, *, radiation, T_mean, T_max, CO2, ARID):
        # FIXME: TT
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
crop = Crop(wheat_yecora_rojo)


def simulate(crop, days=150):
    for d in range(days):
        x = {"radiation": 10, "T_mean": 20, "T_max": 27, "CO2": 400, "ARID": 0.2}
        crop.next_day(**x)
        yield {"day": crop.i, **x, "biomass": crop.biomass}


df = pd.DataFrame([d for d in simulate(crop)]).set_index("day")
px.line(df, y="biomass")
