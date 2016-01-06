SPD
===
__Submitted Picture Downloader__

Downloads every image a redditor has ever submitted.
Currently only works with images uploaded to [imgur](//imgur.com) or [gfycat](//gfycat.com).

Let me know if you need it to work with another site.

#### USAGE
```
./spd.py <redditor name> [download directory]
```

#### NOTES

You need to have `wget` installed and in your path for this to work.

On Windows, you need to have GnuWin `wget` installed to `C:\Program Files (x86)\GnuWin32\bin\wget.exe` (the default)  
You can get it here: http://gnuwin32.sourceforge.net/packages/wget.htm

If SPD downloads an html document by accident, let me know so I can fix it.

Changing the default download directory is probably broken right now.
