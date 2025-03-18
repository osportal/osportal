from setuptools import setup, find_packages

setup(
    name='osportal-CLI',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points="""
        [console_scripts]
        osportal=app.cli.cli:cli
    """,
)
