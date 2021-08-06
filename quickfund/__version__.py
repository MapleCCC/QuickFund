__all__ = ["__version__", "__version_info__"]


__version__ = "v1.4.0"

# TODO Use sophisticated semantic version parsing library
__version_info__ = __version__.lstrip("vV").split(".")
