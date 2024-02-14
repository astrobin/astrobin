import os
import sentry_sdk


SENTRY_DNS = os.environ.get('SENTRY_DNS')

if SENTRY_DNS:
    sentry_sdk.init(
        dsn=SENTRY_DNS,
        enable_tracing=True,
        traces_sample_rate=0.5,
    )
