import os
import zlib
import zstandard
import brotli
import lzma
import shutil
import tempfile
import atexit
import tarfile


# Compression levels to try. For very small files, higher levels are not always the best
ZSTD_LEVELS: tuple[int, ...] = tuple([*range(1, 23)])


# Globals
temp_files: set[str] = set()



class TempFilesManager:
    def __init__(self):
        self.temp_files: list[tuple[str, str | None]] = [] # set[tuple[path, label]]
        at_exit = lambda: self.delete_temp_files()
        atexit.register(at_exit)

    def new_temp_file(self, label: str | None = None):
        file = tempfile.NamedTemporaryFile(delete=False)
        path: str = file.name
        self.temp_files.append((path, label))
        return file

    def delete_temp_files(self) -> None:
        to_delete: list[tuple[str, str | None]] = self.temp_files
        files_count: int = len(to_delete)

        print('Deleting The Below Temp Files:')
        if files_count == 0:
            print('There are no temp files to delete!')
        else:
            for path, label in self.temp_files:
                if label:
                    print(f' - {path} - {label}')
                else:
                    print(f' - {path}')
                os.remove(path)
        


temp_manager = TempFilesManager()


def make_tar(add_path: str, label: str | None = None) -> str:
    tar = temp_manager.new_temp_file(label)
    path: str = tar.name

    if os.path.isfile(add_path):
        with tarfile.open(path, 'w') as t:
            t.add(add_path)
    elif os.path.isdir(add_path):
        with tarfile.open(path, 'w') as t:
            for dir, _, file_names in os.walk(add_path):
                for file_name in file_names:
                    file_path: str = os.path.join(dir, file_name)
                    t.add(file_path)
    else:
        raise RuntimeError(f'Path: "{path}" Does not point to a directory, nor a file!')

    return path


def compress_file_zstd(tar_path: str, level: int) -> str:
    label: str = f'ZSTD level {level}'
    out_file = temp_manager.new_temp_file(label)
    out_file_path: str = out_file.name

    compressor = zstandard.ZstdCompressor(level=level)
    with open(out_file_path, 'wb') as out_f, open(tar_path, 'rb') as in_f:
        compressor.copy_stream(in_f, out_f)

    return out_file_path


def compress_brotli(tar_path: str, level: int) -> str:
    label: str = f'Brotli Level {level}'
    out_file = temp_manager.new_temp_file(label)
    out_file_path: str = out_file.name

    with open(out_file_path, 'wb') as out_f, open(tar_path, 'rb') as in_f:
        compressed = brotli.compress(in_f, quality=level)  # type: ignore
        out_f.write(compressed) # type: ignore
    
    return out_file_path



for i in ZSTD_LEVELS:
    tar: str = make_tar('./sex.txt')
    a = compress_file_zstd(tar, i)
    print(os.path.getsize(a))

print(ZSTD_LEVELS)