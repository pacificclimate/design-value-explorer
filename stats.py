import pstats
from pstats import SortKey

name = "profile-2"
p = pstats.Stats(f'/codebase/{name}.pro')
p.sort_stats(SortKey.TIME).print_stats()
