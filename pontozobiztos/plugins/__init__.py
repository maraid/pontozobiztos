import pathlib

enabled_plugins = [
    "counting_game",
    # "kakiefier",
    "szerenchat",
    # "utility",
    "link_mirror"
]

__all__ = [p.name for p in pathlib.Path(__file__).parent.iterdir()
           if p.is_dir()
           and p.name in enabled_plugins]