# %%
from dataclasses import dataclass, replace
from math import exp

import numpy as np
import pandas as pd
import plotly.express as px


@dataclass(frozen=True)
class Crop:
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

    def fSolar(self, TT, fSolar_max: float = 0.95):
        return min(
            fSolar_max / (1 + exp(-0.01 * (TT - self.I_50A))),
            fSolar_max / (1 + exp(0.01 * (TT - (self.T_sum - self.I_50B)))),
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


wheat_yecora_rojo = Crop(
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

crop = wheat_yecora_rojo

# %%
df = pd.DataFrame([{"T": T, "f(Temp)": crop.fTemp(T)} for T in range(0, 50)]).set_index(
    "T"
)
px.line(df, y="f(Temp)")

# %%
df = pd.DataFrame(
    [{"TT": TT, "f(Solar)": crop.fSolar(TT)} for TT in range(0, 2000, 20)]
).set_index("TT")
px.line(df, y="f(Solar)")

# %%

df = pd.DataFrame(
    [{"T": T, "f(Heat)": crop.fHeat(T)} for T in range(26, 46)]
).set_index("T")
px.line(df, y="f(Heat)")

# %%
df = pd.DataFrame(
    [{"CO2": CO2, "f(CO2)": crop.fCO2(CO2)} for CO2 in range(300, 800, 10)]
).set_index("CO2")
px.line(df, y="f(CO2)")


# %%
# FIXME: (9) updates I_50B
@dataclass(frozen=False)
class Simulation:
    crop: Crop
    day: int = 0
    TT: float = 0
    I_50A: float
    I_50B: float

    def step(self, radiation, *, T_mean, T_max, TT, CO2, ARID):
        biomass_rate = (
            radiation
            * self.fSolar(TT, self.I_50a, self.I_50b)
            * self.RUE
            * self.fCO2(CO2)
            * self.fTemp(T_mean)
            * min(self.fHeat(T_max) * self.fWater(ARID))
        )


simulation = Simulation(wheat_yecora_rojo)
