import glob
import importlib
import os
from collections import namedtuple

from flask import current_app as app
from flask import send_file, send_from_directory, url_for


def register_plugin_assets_directory(app, base_path, endpoint=None):
    """
    Registers a directory to serve assets

    :param app: An osPortal application
    :param string base_path: The path to the directory
    :return:
    """
    base_path = base_path.strip("/")
    if endpoint is None:
        endpoint = base_path.replace("/", ".")

    def assets_handler(path):
        return send_from_directory(base_path, path)

    rule = "/" + base_path + "/<path:path>"
    app.add_url_rule(rule=rule, endpoint=endpoint, view_func=assets_handler)


def register_plugin_asset(app, asset_path, endpoint=None):
    """
    Registers an file path to be served by osPortal

    :param app: An osPortal application
    :param string asset_path: The path to the asset file
    :param boolean admins_only: Whether or not this file should be accessible to the public
    :return:
    """
    asset_path = asset_path.strip("/")
    if endpoint is None:
        endpoint = asset_path.replace("/", ".")

    def asset_handler():
        return send_file(asset_path)

    rule = "/" + asset_path
    app.add_url_rule(rule=rule, endpoint=endpoint, view_func=asset_handler)


def get_plugin_names():
    modules = sorted(glob.glob(app.plugins_dir + "/*"))
    blacklist = {"__pycache__"}
    plugins = []
    for module in modules:
        module_name = os.path.basename(module)
        if os.path.isdir(module) and module_name not in blacklist:
            plugins.append(module_name)
    return plugins


def init_plugins(app):
    """
    Searches for the load function in modules in the app/plugins folder.
    This function is called with the current osPortal app as a parameter.
    This allows osPortal plugins to modify osPortal's behavior.

    :param app: An osPortal application
    :return:
    """
    app.admin_plugin_scripts = []
    app.admin_plugin_stylesheets = []
    app.plugin_scripts = []
    app.plugin_stylesheets = []

    app.admin_plugin_menu_bar = []
    app.plugin_menu_bar = []
    app.plugins_dir = os.path.dirname(__file__)

    for plugin in get_plugin_names():
        module = "." + plugin
        module = importlib.import_module(module, package="app.plugins")
        module.load(app)
        print(" * Loaded module, %s" % module)
