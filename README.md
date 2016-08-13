SPD
===
__Submitted Picture Downloader__

Downloads every image a redditor has ever submitted.
Currently only works with images uploaded to [imgur](//imgur.com) or [gfycat](//gfycat.com).

Let me know if you need it to work with another site.

# NOTE: SPD IS BEING REWRITTEN
The old codebase was buggy and inflexible, largely because it was the second program I'd ever written in Python.\
I'm currently in the process of rewriting it from scratch, hopefully with fewer bugs than before.

#### INSTALLATION

##### Windows
  1.  Download the Python 3 installer: https://www.python.org/downloads/
  2.  Run the installer and follow the on-screen instructions.
  3.  Re-run the installer. Select 'Modify'. Check the 'Add Python environment variables' box.
  4.  Download the `wget` installer: http://gnuwin32.sourceforge.net/packages/wget.htm
  5.  Run the installer and follow the on-screen instructions. Don't modify the install location.
  6.  Download the SPD source zip: https://github.com/skwerlman/SPD/archive/master.zip
  7.  Extract the zip.

To run:
  1.  Open Command Prompt.
  2.  `cd <place where you extracted the zip to>`
  3.  `python spd.py [options] userName`

##### Ubuntu (or other Debian)
  1.  `$ sudo apt-get update && sudo apt-get install python3 git wget`
  2.  `$ cd ~ && git clone https://github.com/skwerlman/SPD.git`

To run:
  1. Press <kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>T</kbd> to open a terminal
  2. `$ cd ~/SPD`
  3. `$ ./spd.py [options] userName`

##### Sabayon
  1.  `# equo up && equo i -av python3 git wget`
  2.  `$ cd ~ && git clone https://github.com/skwerlman/SPD.git`

To run:
  1. `$ cd ~/SPD`
  2. `$ ./spd.py [options] userName`

#### USAGE
```
./spd.py [options] userName
```

#### NOTES

You need to have `wget` installed and in your path for this to work.

On Windows, you need to have GnuWin `wget` on your path or installed to `C:\Program Files (x86)\GnuWin32\bin\wget.exe` (the default)  
You can get it here: http://gnuwin32.sourceforge.net/packages/wget.htm

If SPD downloads an html document by accident, let me know so I can fix it.
