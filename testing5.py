import light_archiver
import pathlib

d = pathlib.Path(r"/home/msikatana-2/Desktop/MEMES-RAHHHHHHHHHH")
i = set(d.iterdir())
out = light_archiver.get_structure(d, i, 0)
print(out)