#!/usr/bin/env python3

import os
import re
import sys

from platform import system as operatingSystem
from subprocess import call
from urllib.request import Request, urlopen
from shutil import which


def getWebPage(url):
    # #
    # Let the user know we are trying to download a webpage
    # Construct a request with a User-Agent header
    # Send the request and read the webpage from the response
    # Convert the webpage from bytes to a string, and return it
    # #
    print('getting: '+url)
    h = Request(url)
    h.add_header('User-Agent', 'SPD/1.0')
    webpage = urlopen(h).read()
    return str(webpage)  # convert from bytes to string


def getSubmittedPage(userName):
    # #
    # Returns the user's submitted page as a string
    # #
    return getWebPage('https://www.reddit.com/user/' +
                      userName +
                      '/submitted/')


def downloadImage(link):
    # #
    # Let the user know we are trying to download an image at the given link
    # Prepare the command (wget) to download the image
    # If wget doesn't exist, and we're on Windows, check whether GnuWin wget
    #     exists but isn't on the path
    #   If it exists, modify the wget command to accommodate
    #   If it doesn't exist, we raise a FileNotFound error
    # Otherwise, if we're on Windows, modify the wget command to avoid an issue
    #     with GnuWin wget and SSL
    # Finally, we run the constructed command to download the image
    # #

    # --no-check-certificate is used on windows because GnuWin wget fails to
    #   verify all certificates for some reason

    print('downloading: ' + link)
    wgetCommand = [which('wget'), '-b', '-N', '-o', '/dev/null', link]
    if which('wget') is None:
        if operatingSystem() == 'Windows' and os.path.isfile(
                'C:\\Program Files (x86)\\GnuWin32\\bin\\wget.exe'):
            wgetCommand = ['C:\\Program Files (x86)\\GnuWin32\\bin\\wget.exe',
                           '-b', '-N', '-o', 'NUL',
                           '--no-check-certificate', link]
        else:
            raise FileNotFoundError('Could not find wget')
    elif operatingSystem() == 'Windows':
        wgetCommand = [which('wget'),'-b', '-N', '-o', 'NUL',
                       '--no-check-certificate', link]

    call(wgetCommand)


def downloadImageGallery(link):
    # #
    # Fetch the HTML page at the given link
    # If it's a gfycat link, alter the url to point at the gif and download it
    # Otherwise, find all '//i.imgur.com' links and download each one
    # #
    webpage = getWebPage(link)
    if re.search(r'gfycat\.com/', link):
        link = link.replace('gfycat', 'giant.gfycat') + '.gif'
        downloadImage(link)
    elif re.search(r'imgur\.com/', link):
        for image in re.findall(
                'src="//(i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|' +
                '[a-zA-Z0-9]{5})\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?)"',
                webpage):
            downloadImage(image)


def isGallery(link):
    # #
    # Check if a link is either an '//imgur.com' or '//gfycat.com' link
    # If so, it's probably HTML so we return true
    # Otherwise, it's a link to an image ('//i.imgur.com'), so we return false
    # #
    if re.match(r'https://(?:imgur\.com/|gfycat\.com/)', link):
        return True
    return False


def getAllImages(webpage):
    # #
    # Find all submitted image links in a page
    # For each one, clean up the link and check if it's a gallery (HTML)
    # If it is, find each relevant image on the page and download it
    # Otherwise, download it directly
    # #
    for link in re.findall(
            '<a class="title may-blank ?" href="(https?://' +
            '(?:gfycat\\.com/[a-zA-Z]+|' +
            'imgur\\.com/(?:[a-zA-Z0-9]{7}|[a-zA-Z0-9]{5})|' +
            'imgur\\.com/a/[a-zA-Z0-9]{5}|' +
            'imgur\\.com/gallery/[a-zA-Z0-9]{5}|' +
            'i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|' +
            '[a-zA-Z0-9]{5})\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?))',
            webpage):

        print('')

        if not re.match(r'https?://', link):
            link = 'https://' + link
        else:
            link = link.replace('http://', 'https://')
        link = link.replace('.gifv', '.gif')  # fix handling of gifv links

        if isGallery(link):
            downloadImageGallery(link)
        else:
            downloadImage(link)


def pageGetNextPage(webpage, userName):
    # #
    # Find the link to the next page, if it exists
    # If it does, download and return the page
    # Otherwise, return None explicitly
    # #
    nextPage = re.findall(
        '(https?://www\\.reddit\\.com/user/' +
        userName +
        '/submitted/\\?count=[0-9]{2,4}&amp;after=t[0-9]_[a-z0-9]{6})',
        webpage)

    if not nextPage == []:
        return getWebPage(nextPage[0].replace('amp;', ''))
    else:
        return None

# -----------------------------------------------------------------------------

userName = sys.argv[1]

# if user provided a download dir, use that instead of the default
if len(sys.argv) > 2:
    basePath = os.path.expanduser(sys.argv[2]) + '/'
else:
    basePath = os.path.expanduser('~/Pictures/SPD/')

# make sure the download directory exists, then change to it
if not os.path.exists(basePath + userName):
    os.makedirs(basePath + userName)
os.chdir(basePath + userName)

# Download all images from the first page
userSubmitted = getSubmittedPage(userName)
getAllImages(userSubmitted)

while True:  # Loop until we can't find a next page link
    userSubmitted = pageGetNextPage(userSubmitted, userName)
    if userSubmitted is None:
        break

    getAllImages(userSubmitted)
