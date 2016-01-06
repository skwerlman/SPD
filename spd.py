#!/usr/bin/env python3

import os
import re
import sys

from platform import system as operatingSystem
from subprocess import call
from urllib.request import Request, urlopen


def getWebPage(url):
    print("\ngetting: "+url)
    h = Request(url)
    h.add_header('User-Agent', 'SPD/1.0')
    webpage = urlopen(h).read()
    return str(webpage)  # convert from bytes to string


def getSubmittedPage(userName):
    return getWebPage('https://www.reddit.com/user/' +
                      userName +
                      '/submitted/')


def downloadImage(link):
    print('downloading: ' + link)
    if operatingSystem() == 'Windows':
        # manually installed wget
        # --no-check-certificate is used because GnuWin wget fails to verify 
        #   all certificates for some reason
        call(['C:\\Program Files (x86)\\GnuWin32\\bin\\wget.exe', '-b',
              '-N', '-o', 'spd.log', '--no-check-certificate', link])
    else:
        # open wget in the background
        call(['wget', '-b', '-N', '-o', 'spd.log', link])


def downloadImageGallery(link):
    webpage = getWebPage(link)
    link = link.replace('http:', 'https:')
    if re.search(r"gfycat\.com/", link):
        link = link.replace('gfycat', 'giant.gfycat') + '.gif'
        downloadImage(link)
    elif re.search(r"imgur\.com/", link):
        for image in getAllImageURLs(webpage):
            downloadImage(image)
    pass


def isGallery(link):
    if re.match(r"https://(?:imgur\.com/|gfycat\.com/)", link):
        return True
    return False


def getAllImageURLs(webpage):
    urlList = re.findall(
        r'src="//(i\.imgur\.com/[a-zA-Z0-9]{7}\.(?:[a-z]{3,4})(?:\?[0-9]+?)?)"',
        webpage)
    return urlList


def getAllImages(webpage):
    for link in re.findall(
            "<a class=\"title may-blank ?\" href=\"(https?://" +
            "(?:gfycat\\.com/[a-zA-Z]+|" +
            "imgur\\.com/(?:[a-zA-Z0-9]{7}|a/[a-zA-Z0-9]{5})|" +
            "i\\.imgur\\.com/[a-zA-Z0-9]{7}\\.(?:[a-z]{3,4})(?:\?[0-9]+?)?))",
            webpage):
        link = link.replace('http:', 'https:')
        if isGallery(link):
            downloadImageGallery(link)
        else:
            downloadImage(link)


def pageGetNextPage(webpage, userName):
    nextPage = re.findall(
        "(https?://www\\.reddit\\.com/user/" +
        userName +
        "/submitted/\\?count=[0-9]{2,4}&amp;after=t[0-9]_[a-z0-9]{6})",
        webpage)
    if not nextPage == []:
        return getWebPage(nextPage[0].replace('amp;', ''))
    else:
        return None

userName = sys.argv[1]
if len(sys.argv) > 2:
    basePath = sys.argv[2]
else:
    basePath = os.path.expanduser("~/Pictures/SPD/")


if not os.path.exists(basePath + userName):
    os.makedirs(basePath + userName)
os.chdir(basePath + userName)

userSubmitted = getSubmittedPage(userName)

getAllImages(userSubmitted)

while True:
    userSubmitted = pageGetNextPage(userSubmitted, userName)
    if userSubmitted is None:
        break

    getAllImages(userSubmitted)
