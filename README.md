# dash-chalice

This package integrates [Plotly Dash](https://dash.plotly.com/) with [AWS Chalice](https://github.com/aws/chalice). It provides a `DashChalice` object which is largely a slot-in replacement for `dash.Dash`, but with the underlying Flask server object replaced with a Chalice one. It aims to provide a more natural path for deployment using AWS Lambda than [Zappa](https://github.com/zappa/Zappa).

A simple example is given below. Note that Chalice expects projects to have a particular structure. To run this example, save the code below as `app.py` and include an empty JSON object `{}` within `.chalice/config.json` in the same directory. The example can then be run locally with `chalice local`.

```python
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash_chalice import DashChalice


dash_app = DashChalice(__name__, title="Example")
dash_app.layout = html.Div(
    [
        dcc.Input(id="input", placeholder="Please type a name"),
        html.Div(id="output"),
    ]
)


@dash_app.callback(
    Output("output", "children"),
    Input("input", "value"),
)
def set_output(input):
    return "Hello!" if input in (None, "") else f"Hello {input}!"


# this needs to be called after the dash app has been set up
dash_app.finalise()

# nb: chalice expects an app variable to be exposed for running/deployment
app = dash_app.server
```

For more information on structuring and deploying apps with Chalice, see the [documentation](https://aws.github.io/chalice/). In addition, you may find [these workshop notes](https://chalice-workshop.readthedocs.io/en/latest/index.html) useful, as I have.
