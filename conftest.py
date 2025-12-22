from hypothesis import HealthCheck, settings
import hypothesis


hypothesis.settings.register_profile(
    "ci",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    max_examples=100,
)
hypothesis.settings.load_profile("ci")
