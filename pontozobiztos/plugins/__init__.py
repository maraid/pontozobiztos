import pathlib

__all__ = [p.name for p in pathlib.Path(__file__).parent.iterdir()
           if p.is_dir()
           and not str(p).endswith("__")
           and not p.name.startswith(".")]