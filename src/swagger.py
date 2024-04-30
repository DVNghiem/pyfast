# -*- coding: utf-8 -*-
from starlette.responses import HTMLResponse, FileResponse
from starlette.applications import Starlette
import os


class SwaggerUI(object):
	def __init__(
		self,
		app: Starlette,
		url='/docs',
		css_url='/swagger-ui/swagger-ui.css',
		js_url='/swagger-ui/swagger-ui-bundle.js',
	) -> None:
		self.app = app
		self.doc_url = url
		self.css_url = css_url
		self.js_url = js_url
		self.setup_route()

	def setup_route(self):
		self.app.add_route(self.doc_url, self.get_html_content, include_in_schema=False)

	def get_css_content(self, request):
		css_path = os.path.dirname(__file__) + '/static/swagger-ui.css'
		print(css_path)
		return FileResponse(css_path)

	def get_js_content(self, request):
		js_path = os.path.dirname(__file__) + '/static/swagger-ui-bundle.js'
		return FileResponse(js_path)

	def get_html_content(self, request):
		title = 'AIT Protocol'
		oauth2_redirect_url = None  # TODO
		html = f"""
                 <!DOCTYPE html>
                 <html>
                 <head>
                 <link type="text/css" rel="stylesheet" href="{self.css_url}">
                 <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
                 <title>{title}</title>
                 </head>
                 <body>
                 <div id="swagger-ui">
                 </div>
                 <script src="{self.js_url}"></script>
                 <!-- `SwaggerUIBundle` is now available on the page -->
                 <script>
                 const ui = SwaggerUIBundle({{
                     url: 'schema',
                 """

		if oauth2_redirect_url:
			html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

		html += """
                     dom_id: '#swagger-ui',
                     presets: [
                     SwaggerUIBundle.presets.apis,
                     SwaggerUIBundle.SwaggerUIStandalonePreset
                     ],
                     layout: "BaseLayout",
                     deepLinking: true,
                     showExtensions: true,
                     showCommonExtensions: true
                 })"""

		html += """
                 </script>
                 </body>
                 </html>
                 """
		return HTMLResponse(html)

	def set_theme(self):
		pass
