# Copyright (c) 2023 Cortext
# %%
from crop_model import CropParameters, Crop

import numpy as np
import pandas as pd
import plotly.express as px

# %%


tomato_sunnySD = CropParameters(
    T_sum=2800,
    HI=0.68,
    I_50A=520,
    I_50B=400,
    T_base=6,
    T_opt=26,
    RUE=1.00,
    I_50maxH=100,
    I_50maxW=5,
    T_heat=32,
    T_ext=45,
    S_CO2=0.07,
    S_water=2.5,
)

crop = Crop(tomato_sunnySD)


def simulate(crop, days=365):
    for _ in range(days):
        x = {
            "radiation": np.random.randint(0, 10),
            "T_mean": np.random.randint(5, 20),
            "CO2": np.random.randint(400, 500),
            "ARID": np.random.uniform(0, 1) ** 3,
        }
        x["T_max"] = x["T_mean"] + np.random.randint(0, 10)
        crop.next_day(**x)
        yield {"day": crop.i, **x, "biomass": crop.biomass}


df = pd.DataFrame([d for d in simulate(crop)]).set_index("day")
px.line(df, y="biomass")

# %%
