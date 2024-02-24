from setuptools import setup

setup(
    name='osportal-CLI',
    version='1.0',
    packages=['app.cli', 'app.cli.commands'],
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points="""
        [console_scripts]
        osportal=app.cli.cli:cli
    """,
)
