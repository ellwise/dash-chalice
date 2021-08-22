from dash import Dash
from dash.exceptions import PreventUpdate, InvalidResourceError
from dash._utils import inputs_to_vals, split_callback_id
import chalice


def to_chalice(response):
    return chalice.Response(
        body=response.response[0],
        status_code=int(response.status.split()[0]),
        headers=dict(response.headers),
    )


class DashChalice(Dash):
    def __init__(self, name=None, server=True, **kwargs):

        # chalice seems to require serve_locally=False
        if "serve_locally" in kwargs:
            raise TypeError(
                "Dash() got an unexpected keyword argument 'serve_locally'"
            )

        super().__init__(server=False, serve_locally=False, **kwargs)

        # We have 3 cases: server is either True (we create the server), False
        # (defer server creation) or a Chalice app instance (we use their
        # server)
        if isinstance(server, chalice.Chalice):
            self.server = server
            if name is None:
                name = getattr(server, "name", "__main__")
        elif isinstance(server, bool):
            name = name if name else "__main__"
            self.server = chalice.Chalice(name) if server else None
        else:
            raise ValueError("server must be a Chalice app or a boolean")

        if self.server is not None:
            self.init_app()

    # this is in place of the equivalent handling in Dash.init_app - it needs
    # to be called after the rest of the server has been set up but before any
    # requests are make
    def finalise(self):
        super()._setup_server()

    # method is rewritten here to avoid flask context exceptions
    def dependencies(self):
        return self._callback_list

    # method is rewritten here to avoid flask context exceptions
    def dispatch(self):
        # below has been taken from parent class, and modified to replace flask
        # with chalice
        try:
            body = self.server.current_request.json_body
            inputs = body.get("inputs", [])
            state = body.get("state", [])
            output = body["output"]
            outputs_list = body.get("outputs") or split_callback_id(output)

            args = inputs_to_vals(inputs + state)

            try:
                func = self.callback_map[output]["callback"]
            except KeyError:
                msg = "Callback function not found for output '{}', perhaps you forgot to prepend the '@'?"  # noqa: E501
                raise KeyError(msg.format(output))
            response = chalice.Response(
                body=func(*args, outputs_list=outputs_list),
                headers={"Content-Type": "application/json"},
            )

        # handle a halted callback and return an empty 204 response
        # this is in place of the equivalent handiling in Dash.init_app
        except PreventUpdate:
            response = chalice.Response(body="", status_code=204)

        return response

    # like parent method, but with a chalice Response
    def serve_layout(self):
        response = super().serve_layout()
        return to_chalice(response)

    # like parent method, but with a chalice Response
    @staticmethod
    def _serve_default_favicon():
        response = Dash._serve_default_favicon()
        return to_chalice(response)

    # like parent method, but with a chalice Response
    def index(self, *args, **kwargs):
        index = super().index(*args, **kwargs)
        return chalice.Response(
            body=index,
            headers={"Content-Type": "text/html"},
        )

    # like parent method, but with a chalice Response
    def serve_component_suites(self, package_name, fingerprinted_path):
        try:
            response = super().serve_component_suites(
                package_name, fingerprinted_path
            )
            response = to_chalice(response)

        # add a handler for components suites errors to return 404
        # this is in place of the equivalent handiling in Dash.init_app
        except InvalidResourceError:
            body, status_code = Dash._invalid_resources_handler(
                InvalidResourceError
            )
            response = chalice.Response(
                body=body,
                status_code=status_code,
            )

        return response

    # this method is based on the equivalent parent method, but heavily
    # modified to register as chalice endpoints
    def init_app(self, app=None):
        """Initialize the parts of Dash that require a chalice app."""

        if app is not None:
            self.server = app

        # nb: below is commented out because it is not used when the kwarg
        # `serve_locally` is False - if included, chalice will fail to deploy
        # because some paths contain the invalid character "@"
        # scripts = self._generate_scripts_html().splitlines()
        # noqa:E501 # endpoints = [tuple(script[31:-11].split("/", 1)) for script in scripts]
        # for package_name, fingerprinted_path in endpoints:
        #     self._add_url(
        #         f"_dash-component-suites/{package_name}/{fingerprinted_path}",
        #         lambda *args, **kwargs: self.serve_component_suites(
        #             package_name, fingerprinted_path
        #         ),
        #     )
        self._add_url("_dash-layout", self.serve_layout)
        self._add_url("_dash-dependencies", self.dependencies)
        self._add_url(
            "_dash-update-component", self.dispatch, methods=["POST"]
        )
        self._add_url("_reload-hash", self.serve_reload_hash)
        self._add_url("_favicon.ico", self._serve_default_favicon)
        self._add_url("", self.index)

        # nb: below is commented out because it is not used when the kwarg
        # `serve_locally` is False - if included, chalice will fail to deploy
        # because the path contains the invalid characters "<", ">", and
        # possibly ":"
        # catch-all for front-end routes, used by dcc.Location
        # self._add_url("<path:path>", self.index)

    # this method is based on the equivalent parent method, but heavily
    # modified to register as chalice endpoints
    def _add_url(self, name, view_func, methods=("GET",)):
        full_name = self.config.routes_pathname_prefix + name
        kwargs = {
            "kwargs": {
                "methods": list(methods),
                "content_types": ["application/json"],
            },
            "path": full_name,
        }
        self.server._register_route(full_name, view_func, kwargs)

        # record the url in Dash.routes so that it can be accessed later
        # e.g. for adding authentication with flask_login
        self.routes.append(full_name)
