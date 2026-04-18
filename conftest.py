# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import hypothesis
from hypothesis import HealthCheck

pytest_plugins = ["provide.testkit.process.fixtures"]


hypothesis.settings.register_profile(
    "ci",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    max_examples=100,
)
hypothesis.settings.load_profile("ci")
