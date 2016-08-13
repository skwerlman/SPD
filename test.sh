#!/bin/bash -x

# try to download a broken image link
python3 spd.py skwerlman -D  &&
python3 spd.py skwerlman -D -F False  &&

# try to download a fake gallery
python3 spd.py -g gallery/00000 -D &&
python3 spd.py -g gallery/00000 -D -F False &&

# download A LOT of images
python3 spd.py -g gallery/nroxr -D &&
python3 spd.py -g gallery/nroxr -D -F False &&

exit 0

echo 'FAILED'
# todo need more tests
