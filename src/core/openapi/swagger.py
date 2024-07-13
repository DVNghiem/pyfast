# -*- coding: utf-8 -*-
from robyn.robyn import Response
from robyn.templating import TemplateInterface


class SwaggerUI(TemplateInterface):
	def __init__(
		self,
		title='Swagger',
		css_url='/swagger-ui/swagger-ui.css',
		js_url='/swagger-ui/swagger-ui-bundle.js',
	) -> None:
		self.title = title
		self.css_url = css_url
		self.js_url = js_url

	def render_template(self, *args, **kwargs) -> Response:
		return Response(
			status_code=200,
			headers={'Content-Type': 'text/html'},
			description=self.get_html_content(),
		)

	def get_html_content(self):
		oauth2_redirect_url = None  # TODO
		html = f"""
                 <!DOCTYPE html>
                 <html>
                 <head>
                 <link type="text/css" rel="stylesheet" href="{self.css_url}">
                 <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
                 <title>{self.title}</title>
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
		return html
