"""Generate realistic NovaCommerce customers."""

from __future__ import annotations
import numpy as np
import pandas as pd
from faker import Faker

from data_generator.config import GeneratorConfig, SEGMENTS, CHANNELS


# US state distribution weighted toward population centres
_STATES = [
    ("CA", 0.12), ("TX", 0.09), ("FL", 0.08), ("NY", 0.07), ("PA", 0.05),
    ("IL", 0.05), ("OH", 0.04), ("GA", 0.04), ("NC", 0.04), ("MI", 0.03),
    ("WA", 0.03), ("AZ", 0.03), ("MA", 0.03), ("TN", 0.02), ("IN", 0.02),
    ("MO", 0.02), ("MD", 0.02), ("WI", 0.02), ("MN", 0.02), ("CO", 0.02),
]
_STATE_CODES = [s for s, _ in _STATES]
_STATE_WEIGHTS = [w for _, w in _STATES]
_REMAINING_WEIGHT = 1.0 - sum(_STATE_WEIGHTS)
# distribute remaining across 30 other states
_OTHER_STATES = [
    "AL", "AK", "AR", "CT", "DE", "HI", "ID", "IA", "KS", "KY",
    "LA", "ME", "MT", "NE", "NV", "NH", "NJ", "NM", "ND", "OK",
    "OR", "RI", "SC", "SD", "UT", "VT", "VA", "WV", "WY", "DC",
]
_STATE_CODES += _OTHER_STATES
_STATE_WEIGHTS += [_REMAINING_WEIGHT / len(_OTHER_STATES)] * len(_OTHER_STATES)


def generate(cfg: GeneratorConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    fake = Faker("en_US")
    fake.seed_instance(cfg.seed)

    n = cfg.customers
    date_range = pd.date_range(cfg.start_date, cfg.end_date)

    # Signup dates — more signups in later periods (growth trend)
    weights = np.linspace(0.5, 2.0, len(date_range))
    weights /= weights.sum()
    signup_dates = rng.choice(date_range, size=n, p=weights)

    states = rng.choice(_STATE_CODES, size=n, p=_STATE_WEIGHTS)

    segments = rng.choice(
        SEGMENTS,
        size=n,
        p=[0.15, 0.25, 0.15, 0.20, 0.25],   # Champions, Loyal, At-Risk, Promising, New
    )

    channels = rng.choice(
        CHANNELS,
        size=n,
        p=[0.30, 0.25, 0.20, 0.10, 0.08, 0.04, 0.03],
    )

    records = []
    for i in range(n):
        profile = fake.simple_profile(sex=None)
        records.append({
            "customer_id":          f"CUST-{i + 1:07d}",
            "first_name":           profile["name"].split()[0],
            "last_name":            profile["name"].split()[-1],
            "email":                profile["mail"],
            "signup_date":          pd.Timestamp(signup_dates[i]).date(),
            "country":              "US",
            "state":                states[i],
            "city":                 fake.city(),
            "customer_segment":     segments[i],
            "acquisition_channel":  channels[i],
        })

    df = pd.DataFrame(records)
    df["customer_id"] = df["customer_id"].astype(str)
    return df
