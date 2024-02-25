import os
import sentry_sdk


SENTRY_DNS = os.environ.get('SENTRY_DNS')
TRACE_SAMPLE_RATE = 1.0 if DEBUG else 0.2
PROFILES_SAMPLE_RATE = 1.0 if DEBUG else 0.1

if SENTRY_DNS:
    sentry_sdk.init(
        dsn=SENTRY_DNS,
        enable_tracing=True,
        traces_sample_rate=TRACE_SAMPLE_RATE,
        profiles_sample_rate=PROFILES_SAMPLE_RATE,
    )
