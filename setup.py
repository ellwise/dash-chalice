from setuptools import setup
from os import path


# read the contents of your README file
curr_dir = path.abspath(path.dirname(__file__))
with open(path.join(curr_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="dash-chalice",
    version="0.1.1",
    description="Chalice as an alternative to Flask for Plotly Dash",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ellwise/dash-chalice",
    author="Elliott Wise",
    author_email="ell.wise@gmail.com",
    license="GNU GPL v3",
    packages=["dash_chalice"],
    install_requires=["dash", "chalice"],
    include_package_data=True,
    zip_safe=False,
)
