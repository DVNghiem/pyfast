# -*- coding: utf-8 -*-
from typing import Any, List
from robyn import Robyn
from src.core.route import RouteSwagger
from src.apis import routes

import logging
import contextlib

class Application:
	def __init__(self, routes: List[RouteSwagger], *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)

		self.app = Robyn(__file__)
		GLOBAL_DEPENDENCY = "GLOBAL DEPENDENCY"

		self.app.inject_global(GLOBAL_DEPENDENCY=GLOBAL_DEPENDENCY)
		for route in routes:
			self.app.router.routes.extend(route(self.app).get_routes())
	
	def start(self, host, port):
		self.app.start(host=host, port=port)

app = Application(routes=routes)
