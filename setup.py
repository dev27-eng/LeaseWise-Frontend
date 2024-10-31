from setuptools import setup, find_packages

setup(
    name="leasecheck",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=2.0.0",
        "requests>=2.32.0",
    ],
    python_requires=">=3.8",
    package_data={
        "leasecheck": [
            "templates/*.html",
            "static/css/*.css",
            "static/images/*"
        ],
    },
)
