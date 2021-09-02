import pathlib

enabled_plugins = [
    "counting_game",
    # "kakiefier",
    "szerenchat",
    # "utility",
    # "webapp_link_provider",
    "link_mirror",
    "repost",
    "link_preview",
    # "forbidden_words",
    "nostalga",
    "archive",
    "ping"
]

__all__ = [p.name for p in pathlib.Path(__file__).parent.iterdir()
           if p.is_dir()
           and p.name in enabled_plugins]
