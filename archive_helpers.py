"""This file contains functions that can be used for making file archives"""


def make_light_archive():
    """Light archives is a custom format written for this script.
    It ignores metadata and aims to save every single byte
    However it is not perfect.
    
    
    * block size is in bytes
    * Type is a byte representing the type of an archive's entry : 
    - 0xxxxxxx->file here
    - 1xxxxxxx->folder here -> a folder automatically puts the program inside it; folders are ALWAYS to be stored AFTER files on the same depth
    - the xxxxxxx is a number representing 'how many times to go back up' -> due to this the 'SAFE' supported depth of the archive is 128
    * The order of the entries matters, they are read from left to right
    * Padding is added only if necessary so that the amount of blocks is respected

    * ARCHIVE SWITCH 1 :
    - 0 - deep archive - supports depth and folders
    - 1 - shallow archive - only files
    * ARCHIVE SWITCH 2 :
    - 0 - blocks - the archive will have blocks
    - 1 - no blocks - the archive will not have blocks (a special escape sequence of bytes will be used instead)
    TODO: the sequence of bytes should be generated to be as small as possible
    * ARCHIVE SWITCH 3 :
    - 0 - big blocks - all blocks and amounts of blocks will have variable amounts of bytes in length (for large files) 
    - 1 - small blocks - all blocks and amounts of blocks will have one byte in length (for small files)

    TODO: ACTUALLY FUCK BLOCKS. THEY ARE NOT USEFUL. THEIR SIZE VARIES AND IT'S LITERALLY JUST MULTIPLICATION AND THE THING WITH ...
    TODO: ... MULTIPLICATION IS THAT IT CAN RARELY BE SHORTENED WITHOUT DECIMALS ESPECIALLY WHEN THERE ARE MORE THAN 3 FILES ...
    TODO: ... I SHOULD JUST DEFINE THE LENGTHS OF THE FILES IN BYTES
    TODO: A PROBLEM IS THAT THE LENGTH WILL NEED TO BE ESCAPED SOMEHOW
    TODO: I SHOULD HAVE ONLY 1 SWITCH MAYBE - SHALLOW AND DEEP +
    TODO: MAYBE USE THE REST OF THE 7 BITS TO GIVE THE ARCHIVE A HINT OF 'how long the lengths/names are in bytes' SO THAT I CAN AVOID THE 00000000 WASTE


    SHARED BETWEEN TYPES
    ( { ARCHIVE SWITCH 1 } { ARCHIVE SWITCH 2 } + Block Size ) ( 00000000 )

    TYPE 0
    [ TYPE 1 ] ( AMOUNT OF BLOCKS 1 ) [ 00000000 ] ( NAME1 ) [ 00000000 ] ( FILE DATA 1 ) ( PADDING 1 )   <- file entry
    [ TYPE 2 ] ( NAME2 ) [ 00000000 ] <- folder entry
    [ TYPE 3 ] ( AMOUNT OF BLOCKS 3 ) [ 00000000 ] ( NAME3 ) [ 00000000 ] ( FILE DATA 3 ) ( PADDING 3 )   <- file entry inside the folder


    






















    The format's structure looks like this:
    [] -> single byte
    () -> chain of bytes
    {} -> single reserved bit
    ?xyz? -> optional - only present if necessary / on specific conditions
    ... -> repeat the previous byte as many times as necessary
    <- -> comment

    
    ( NAME ) [ NAME TERMINATOR ]
    ?( TYPE )? <- only present if it's the #1 Terminator
    ( [ LENGTH { IS ENDING } ] ... )
    ( DATA )

    Here is how the TYPE looks (if it's present)
    ( [ { IS FOLDER } xxxxxx { IS ENDING } ] ? [ xxxxxxxx { IS ENDING } ] ... ? )
    the xxx... - when contatenated this will be a number representing "how many times to go back"

    NAME TERMINATORS:
    - #0 - [ 00000000 ] - this means that it's a file and that xxx... is 0 -> the TYPE bytes are skipped (saves 1-2 bytes)
    - #1 - [ 00101111 ] - this means that it's NOT a file and/or the xxx is NOT 0 -> the TYPE bytes are present
    *[ 00101111 ] is an '/' utf-8 character). This is the only utf8 character which cannot be uses in both ext4 and ntfs filenames

    If it's is a folder => the program automatically "goes" inside it => this is why the archive should always sorts folders to be last

    Here is what the xxx... number would be for each entry in an example archive:
    *on the right side there will be the bytes 'representing' the file
    0  file         | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  folder       | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 10000001 ]
    0  /   file     | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /   folder   | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 10000001 ]
    0  /   /   file | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    1  /  file      | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 00000011 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /  folder    | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 10000001 ]
    0  /   /  file  | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    2  folder       | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 10000101 ]
    0  /  file      | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /  Imagine 130 folders inside each other here
    131folder       | ( FILE NAME ) [ NAME TERMINATOR #1 ] [ 10000010 ] [ 00000111 ] <- 131 in base2 is 10000011
    0  /  file      | ( FILE NAME ) [ NAME TERMINATOR #0 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )

    """
