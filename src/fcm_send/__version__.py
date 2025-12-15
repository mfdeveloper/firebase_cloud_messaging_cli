"""Version information for fcm-send package."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fcm-send")
except PackageNotFoundError:
    # Package is not installed (running from source without install)
    __version__ = "0.0.0.dev"

