# -*- coding: utf-8 -*-
from typing import Optional
from pyfast.core import logger

import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration


def setup(dsn: Optional[str] = None) -> None:
    if dsn:
        logger.debug(dsn)
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
            ],
            traces_sample_rate=1.0,
            send_default_pii=True,
            enable_tracing=True,
            send_client_reports=False,
        )
        logger.debug("Config sentry successfully")

    else:
        logger.debug("Sentry not config")
