import pathlib

enabled_plugins = [
    "counting_game",
    # "google_sheets",
    # "kakiefier",
    # "szerenchat",
    "utility"
]

__all__ = [p.name for p in pathlib.Path(__file__).parent.iterdir()
           if p.is_dir()
           and p.name in enabled_plugins]