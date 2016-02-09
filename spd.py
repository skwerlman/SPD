#!/usr/bin/env python3

import os
import re
import sys
import colorama
import time

from platform import system as operatingSystem

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from shutil import which
from subprocess import call
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class ArgumentException(Exception): pass


class Color:
    reset = "\033[0m"
    fggreen = "\033[32m"
    fgblue = "\033[34m"
    fglightred = "\033[91m"
    fglightyellow = "\033[93m"
    fglightblue = "\033[94m"
    fgwhite = "\033[97m"

    def colorize(self, code, message):
        return code + message + self.reset


class Logger:
    INFO = 1
    WARNING = 4
    ERROR = 8

    color = Color()

    def log(self, level, message):
        code = ""
        message = str(message)

        if level == self.INFO:
            code = self.color.fgwhite

        elif level == self.WARNING:
            code = self.color.fglightyellow
            message = 'WARNING:   ' + message

        elif level == self.ERROR:
            code = self.color.fglightred
            message = 'ERROR:   ' + message

        print(self.color.colorize(code, message))


def getWebPage(url):
    '''
    # Let the user know we are trying to download a webpage
    # Construct a request with a User-Agent header
    # Send the request and read the webpage from the response
    # Convert the webpage from bytes to a string, and return it
    '''
    url = cleanLink(url, args)
    log(logger.INFO, 'getting: ' + url)
    h = Request(url)
    h.add_header('User-Agent', 'SPD/1.0')
    try:
        webpage = urlopen(h).read()
    except HTTPError as e:
        log(logger.WARNING, 'a problem occured when getting ' + url)
        if e.code == 404:
            message = 'the requested page could not be found'
        else:
            message = 'the server returned a code of ' + str(e.code)
        log(logger.WARNING, message)
        webpage = ''  # make sure we still pass a valid value
    return str(webpage)  # convert from bytes to string


def getSubmittedPage(args):
    '''
    # Returns the user's submitted page as a string
    '''
    return getWebPage(args.submitted_page_pattern.format(args.userName))


def downloadImage(link, args):
    '''
    # Let the user know we are trying to download an image at the given link
    # Prepare the command (wget) to download the image
    # If wget doesn't exist, and we're on Windows, check whether GnuWin wget
    #     exists but isn't on the path
    #   If it exists, modify the wget command to accommodate
    #   If it doesn't exist, we raise a FileNotFound error
    # Otherwise, if we're on Windows, modify the wget command to avoid an issue
    #     with GnuWin wget and SSL
    # Finally, we run the constructed command to download the image
    '''

    # --no-check-certificate is used on windows because GnuWin wget fails to
    #   verify all certificates for some reason

    link = cleanLink(link, args)

    log(logger.INFO, 'downloading: ' + link)
    wgetCommand = [which('wget'), '-b', '-N', '-o', '/dev/null', link]
    if (not args.skip_gnuwin_wget) and (which('wget') is None):
        if operatingSystem() == 'Windows' and os.path.isfile(
                'C:\\Program Files (x86)\\GnuWin32\\bin\\wget.exe'):
            wgetCommand = ['C:\\Program Files (x86)\\GnuWin32\\bin\\wget.exe',
                           '-b', '-N', '-o', 'NUL',
                           '--no-check-certificate', link]
        else:
            print(logger.color.fglightred)
            raise FileNotFoundError('Could not find wget')
    elif operatingSystem() == 'Windows':
        wgetCommand = [which('wget'), '-b', '-N', '-o', 'NUL',
                       '--no-check-certificate', link]

    time.sleep(.05)
    call(wgetCommand)


def downloadImageGallery(link, args):
    '''
    # Fetch the HTML page at the given link
    # If it's a gfycat link, alter the url to point at the gif and download it
    # Otherwise, find all '//i.imgur.com' links and download each one
    '''
    webpage = getWebPage(link)
    if re.search(r'gfycat\.com/', link):
        if not re.search(r'\.gif', link):
            link = link.replace('gfycat', 'giant.gfycat') + '.gif'
        downloadImage(link, args)
    elif re.search(r'imgur\.com/', link):
        if webpage == '' and re.search(r'layout/grid', link):
            log(logger.WARNING, 'grid layout not found, trying again')
            webpage = getWebPage(link.replace('/layout/grid', ''))
            for image in re.findall(
                    args.imgur_gallery_image_regex,
                    webpage):
                downloadImage(image, args)
        else:
            for image in re.findall(
                    args.imgur_grid_image_regex,
                    webpage):
                downloadImage(image, args)


def cleanLink(link, args):
    if not re.match(r'https?://', link):
        link = 'https://' + link
    else:
        link = link.replace('http://', 'https://')
    if args.gifv_as_gif:
        link = link.replace('.gifv', '.gif')
    if args.webm_as_gif:
        link = link.replace('.webm', '.gif')
    if args.clean_imgur_links:
        link = link.replace('?1', '')
    if args.imgur_force_grid:
        if re.search(r'[a-zA-Z0-9]{7}[bs]\.', link):
            link = link.replace('b.', '.')
            link = link.replace('s.', '.')
    return link


def isGallery(link, args):
    '''
    # Check if a link is (by default) an '//imgur.com' or '//gfycat.com' link
    # If so, it's probably HTML so we return true
    # Otherwise, it's a link to an image (e.g. '//i.imgur.com'),
    #   so we return false
    '''
    if re.match(args.gallery_regex, link):
        return True
    return False


def getAllImages(webpage, args):
    '''
    # Find all submitted image links in a page
    # For each one, clean up the link and check if it's a gallery (HTML)
    # If it is, find each relevant image on the page and download it
    # Otherwise, download it directly
    '''
    for link in re.findall(args.image_link_regex, webpage):

        print('')

        link = cleanLink(link, args)

        if isGallery(link, args):
            if re.search(r'imgur\.com', link):
                    if args.imgur_force_grid:
                        if not re.search(r'/layout/grid/?$', link):
                            link = link + '/layout/grid'
            downloadImageGallery(link, args)
        else:
            downloadImage(link, args)


def pageGetNextPage(webpage, args):
    '''
    # Find the link to the next page, if it exists
    # If it does, download and return the page
    # Otherwise, return None explicitly
    '''
    nextPage = re.findall(
        args.next_page_regex.format(args.userName),
        webpage)

    if not nextPage == []:
        return getWebPage(nextPage[0].replace('amp;', ''))
    else:
        return None


def actionDownloadSubmittedImages(args):
    # Download all images from the first page
    userSubmitted = getSubmittedPage(args)
    getAllImages(userSubmitted, args)

    if args.recursive:  # misnomer
        while True:  # Loop until we can't find a next page link
            userSubmitted = pageGetNextPage(userSubmitted, args)
            if userSubmitted is None:
                break

            getAllImages(userSubmitted, args)


def actionDownloadImgurGallery(args):
    if not re.match(
            r"^(?:a/|gallery/|)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            args.gallery):
        raise ArgumentException(
            "GALLERY should be a valid Imgur URL without 'imgur.com/'")

    url = 'https://imgur.com/' + args.gallery

    if args.imgur_force_grid:
        if not re.search(r'/layout/grid/?$', url):
            url = url + '/layout/grid'

    downloadImageGallery(url, args)


def t_or_f(arg):
    # handle 'bool' args
    ua = str(arg)
    if ua == 'True':
        return True
    elif ua == 'False':
        return False
    else:
        return ua


def is_gal(arg):
    # handle gallery args
    ua = str(arg)
    if not re.match(
            r"^(?:a/|gallery/|)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            arg):
        parser.error('invalid GALLERY')
    return ua


def is_uname(arg):
    # handle username args
    ua = str(arg)
    if re.match(
            r"^(?:a/|gallery/)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            arg):
        parser.error('invalid USERNAME')
    return ua


# -----------------------------------------------------------------------------


parser = ArgumentParser(
    description='SPD: Download every image a redditor ' +
                'has submitted (ever)',
    usage='%(prog)s [options] ( USERNAME | -g GALLERY )',
    formatter_class=ArgumentDefaultsHelpFormatter)

positionalGroup = parser.add_mutually_exclusive_group(required=True)

winArgGroup = parser.add_argument_group(
    title='Windows arguments',
    description='These options do nothing outside of Windows.')

advArgGroup = parser.add_argument_group(
    title='advanced arguments',
    description='These options change how SPD reads a webpage. ' +
    'They require intimate knowledge of the pages you are searching. ' +
    'Use caution with these!')

# positional args
positionalGroup.add_argument(
    'userName',
    type=is_uname,
    nargs='?',
    help='The name of the redditor whose images ' +
         'you\'d like to download')

positionalGroup.add_argument(
    '-g', '--gallery',
    type=is_gal,
    help='The URL to the Imgur gallery you\'d like to download, ' +
         'minus \'https://imgur.com/\'')

# optional args
parser.add_argument(
    '-d',
    type=str,
    help='The directory to save the images in. ' +
         '<userName> is appended to this value.',
    default='~/Pictures/SPD',
    dest='directory')

parser.add_argument(
    '-r', '--recursive',
    help='',  # Lack of help is intentional; see -n
    action='store_true',
    default=True,
    dest='recursive')

parser.add_argument(
    '-n', '--no-recursive',
    help='Sets whether SPD should iterate over all of the user\'s ' +
         'submitted pages, or just parse the fist one. ' +
         'If more than one of -n or -r is specified, ' +
         'the last one will take effect.',
    action='store_false',
    default=True,
    dest='recursive')

parser.add_argument(
    '-D', '--imgur-force-grid',
    choices=[True, False],
    type=t_or_f,
    help='Whether to use the grid layout when looking at a gallery.',
    default=True)

parser.add_argument(
    '-G', '--gifv-as-gif',
    choices=[True, False],
    type=t_or_f,
    help='Whether to download GIFV files on Imgur as GIFs.',
    default=True)

parser.add_argument(
    '-W', '--webm-as-gif',
    choices=[True, False],
    type=t_or_f,
    help='Whether to download WEBM files on Imgur as GIFs.',
    default=True)

parser.add_argument(
    '-C', '--clean-imgur-links',
    choices=[True, False],
    type=t_or_f,
    help='Whether to strip the \'?1\' from the end of Imgur links.',
    default=True)

# Windows args
winArgGroup.add_argument(
    '--skip-gnuwin-wget',
    help='Skips looking for GnuWin wget if wget is ' +
         'not in %%PATH%%.',
    action='store_true',
    default=False)

# advanced args
advArgGroup.add_argument(
    '--gallery-regex',
    type=str,
    help='Sets a custom regex for testing if a link is a gallery.',
    default=r'https://(?:imgur\.com/|gfycat\.com/)',
    metavar='REGEX')

advArgGroup.add_argument(
    '--imgur-gallery-image-regex',
    type=str,
    help='Sets a custom regex for finding all images in an Imgur gallery. ' +
         '(original layout)',
    default='src="//(i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|' +
            '[a-zA-Z0-9]{5})\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?)"',
    metavar='REGEX')

advArgGroup.add_argument(
    '--imgur-grid-image-regex',
    type=str,
    help='Sets a custom regex for finding all images in an Imgur gallery. ' +
         '(grid layout)',
    default='data-src="//(i\\.imgur\\.com/[a-zA-Z0-9]{8}' +
            '\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?)"',
    metavar='REGEX')

advArgGroup.add_argument(
    '--image-link-regex',
    type=str,
    help='Sets a custom regex for finding all images on the user\'s ' +
         'submitted page.',
    default='<a class="title may-blank ?" href="(https?://' +
            '(?:gfycat\\.com/[a-zA-Z]+?|' +
            'giant\\.gfycat\\.com/[a-zA-Z]+?\\.gif|' +
            'imgur\\.com/(?:[a-zA-Z0-9]{7}|[a-zA-Z0-9]{5})|' +
            'imgur\\.com/a/[a-zA-Z0-9]{5}|' +
            'imgur\\.com/gallery/[a-zA-Z0-9]{5}|' +
            'i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|[a-zA-Z0-9]{5})' +
            '\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?))"',
    metavar='REGEX')

advArgGroup.add_argument(
    '--next-page-regex',
    type=str,
    help='Sets the regex used to find the URL for the next page. ' +
         'The first \'{!s}\' is replaced by the user\'s name. ' +
         'All other {\'s and }\'s should be doubled up. ' +
         'See https://docs.python.org/3/library/string.html#formatspec',
    default='https?://www\\.reddit\\.com/user/{!s}' +
            '/submitted/\\?count=[0-9]{{2,4}}&amp;after=t[0-9]_[a-z0-9]{{6}}',
    metavar='REGEX')

advArgGroup.add_argument(
    '--submitted-page-pattern',
    type=str,
    help='Sets the pattern used to construct the link to the user\'s ' +
         'submitted page. ' +
         'The first \'{!s}\' is replaced by the user\'s name.',
    default='https://www.reddit.com/user/{!s}/submitted/',
    metavar='PATTERN')

args = parser.parse_args()

if args.userName:
    downloadDirectory = os.path.expanduser(args.directory +
                                           '/' + args.userName)
elif args.gallery:
    downloadDirectory = os.path.expanduser(args.directory +
                                           '/gallery/' + args.gallery)

colorama.init()
logger = Logger()
log = logger.log

# make sure the download directory exists, then change to it
if not os.path.exists(downloadDirectory):
    os.makedirs(downloadDirectory)
os.chdir(downloadDirectory)

if args.userName:
    actionDownloadSubmittedImages(args)
elif args.gallery:
    actionDownloadImgurGallery(args)
