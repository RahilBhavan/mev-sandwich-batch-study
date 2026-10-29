"""Hypothesis settings. CI selects the "ci" profile with a fixed seed: pytest --hypothesis-profile=ci --hypothesis-seed=0."""
import os

from hypothesis import HealthCheck, settings

_common = dict(deadline=None, database=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
settings.register_profile("dev", max_examples=200, **_common)
settings.register_profile("ci", max_examples=500, print_blob=True, **_common)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
