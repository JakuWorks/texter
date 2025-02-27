from pathlib import Path
import light_archiver

src = r'/home/msikatana-2/Desktop/'
a = Path(f"{src}/destin.light")
des = Path(f"{src}/result/")
light_archiver.unpack_light_archive(a, des)