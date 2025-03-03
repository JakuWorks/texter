import light_archiver
from pathlib import Path
dest = r'/home/msikatana-2/Desktop/destin.light'
src = r'/home/msikatana-2/Desktop/inputt/'
# f1 = fr'{src}/a.txt'
# f2 = fr'{src}/b.txt'
# f3 = fr'{src}/c.txt'
# light_archiver.make_light_archive(Path(dest), Path(src), [Path(f1), Path(f2), Path(f3)])
d1 = fr'{src}/1/'
d2 = fr'{src}/a/'
d3 = fr'{src}/e/'
d4 = fr'{src}froot'
light_archiver.make_light_archive(Path(dest), Path(src), [Path(d1), Path(d2), Path(d3), Path(d4)])

# light_archiver.get_encoded_int(4)
