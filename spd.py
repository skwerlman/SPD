#!/usr/bin/env python3

import os
import re
import time

from platform import system as operating_system

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from bs4 import BeautifulSoup
from shutil import which
from subprocess import call
from traceback import format_exc
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zenlog import log

if operating_system() == 'Windows':
    log.d('on windows, importing colorama')
    import colorama
    colorama.init()


class ArgumentException(Exception):
    pass


class WGetNotFoundException(Exception):
    pass


def get_web_page(url):
    '''
    # Let the user know we are trying to download a webpage
    # Construct a request with a User-Agent header
    # Send the request and read the webpage from the response
    # Convert the webpage from bytes to a string, and return it
    '''
    url = clean_link(url)
    log.i('getting: ' + url)
    handle = Request(url)
    handle.add_header('User-Agent', 'SPD/1.0')
    try:
        webpage = urlopen(handle).read()
    except HTTPError as err:
        log.w('a problem occured when getting ' + url)
        if err.code == 404:
            message = 'the requested page could not be found'
        else:
            message = 'the server returned a code of ' + str(err.code)
        log.w(message)
        webpage = str(err.code)  # pass the return code as a string
    webpage = str(webpage)  # convert from bytes to string
    log.d(len(webpage))
    soup = BeautifulSoup(webpage, 'html.parser')
    return soup


def get_submitted_page():
    '''
    # Returns the user's submitted page as a string
    '''
    global args
    return get_web_page(args.submitted_page_pattern.format(args.user_name))


def download_image(link):
    '''
    # Let the user know we are trying to download an image at the given link
    # Prepare the command (wget) to download the image
    # If wget doesn't exist, we raise a FileNotFound error
    # Otherwise, if we're on Windows, modify the wget command to avoid an issue
    #     with GnuWin wget and SSL
    # Finally, we run the constructed command to download the image
    '''

    global args

    # --no-check-certificate is used on windows because GnuWin wget fails to
    #   verify all certificates for some reason

    link = clean_link(link)

    log.i('downloading: ' + link)
    wget_command = [which('wget'), '-b', '-N', '-o', '/dev/null', link]
    if (which('wget') is None):
        raise WGetNotFoundException('Could not find wget')
    elif operating_system() == 'Windows':
        log.d('on windows, adjusting wget_command')
        wget_command = [which('wget'), '-b', '-N', '-o', 'NUL',
                        '--no-check-certificate', link]

    try:
        while call(wget_command) != 0:
            time.sleep(.05)
            log.d('call is not 0')
            log.i('retrying...')
    except BlockingIOError:
        time.sleep(.1)
        log.d('BlockingIOError!')
        log.w('retrying...')
        download_image(link)


def download_image_gallery(link):
    '''
    # Fetch the HTML page at the given link
    # If it's a gfycat link, alter the url to point at the gif and download it
    # Otherwise, find all '//i.imgur.com' links and download each one
    '''
    global args
    if 'gfycat.com/' in link:
        log.d('page is gfycat')
        if not re.search(r'\.(gif|webm)', link):
            link = link.replace('gfycat', 'fat.gfycat') + '.webm'
        download_image(link)
    elif 'imgur.com/' in link:
        webpage = get_web_page(link)
        if str(webpage) == '404' and re.search(r'layout/grid', link):
            log.w('grid layout not found, trying again')
            webpage = get_web_page(link.replace('/layout/grid', ''))
            log.d('page is imgur gallery (limited to first 20 images!)')
            urls = webpage.find_all('a')
            for url in urls:
                if re.search(args.imgur_gallery_image_regex, url.get('href')):
                    log.d('matched imgur_gallery_image_regex in %s' % url)
                    download_image(url.get('href'))
        else:
            log.d('page is imgur grid')
            urls = webpage.find_all('img')
            for url in urls:
                if url.get('data-src'):
                    if re.search(args.imgur_grid_image_regex, url.get('data-src')):
                        log.d('matched data-src in %s, grid image link' % url)
                        download_image(url.get('data-src'))
                elif url.get('src'):
                    if re.search(args.imgur_gallery_image_regex, url.get('src')):
                        log.d('matched src in %s, gallery image link' % url)
                        download_image(url.get('src'))
                else:
                    log.d('no src, data-src in %s' % url)


def clean_link(link):
    global args
    log.d('cleaning link')
    old_link = link
    if not re.match(r'https?://', link):
        link = 'https://' + link
    else:
        link = link.replace('http://', 'https://')
    if args.gifv_as_gif:
        link = link.replace('.gifv', '.gif')
    if args.webm_as_gif:
        link = link.replace('.webm', '.gif')
        if '.gfycat.com/' in link:  # fix when config
            link = link.replace('//zippy.', '//giant.')
            link = link.replace('//fat.', '//giant.')
    if args.clean_imgur_links:
        link = link.replace('?1', '')
    if args.imgur_force_grid:
        if re.search(r'[a-zA-Z0-9]{7}[bs]\.', link):
            link = link.replace('b.', '.')
            link = link.replace('s.', '.')
    link = link.replace('////', '//')
    log.d('%s => %s' % (old_link, link))
    return link


def is_gallery(link):
    '''
    # Check if a link is (by default) an '//imgur.com' or '//gfycat.com' link
    # If so, it's probably HTML so we return true
    # Otherwise, it's a link to an image (e.g. '//i.imgur.com'),
    #   so we return false
    '''
    global args
    if re.match(args.gallery_regex, link):
        return True
    return False


def get_all_images(webpage):
    '''
    # Find all submitted image links in a page
    # For each one, clean up the link and check if it's a gallery (HTML)
    # If it is, find each relevant image on the page and download it
    # Otherwise, download it directly
    '''
    global args
    urls = webpage.find_all('a')
    for url in urls:
        if url.get('href'):
            link = url.get('href')
        else:
            link = ''
        if re.search(args.image_link_regex, link):
            if 'title' in url.get('class'):

                print('')  # why is this here????

                link = clean_link(link)

                if is_gallery(link):
                    if re.search(r'imgur\.com', link) and args.imgur_force_grid:
                        if not re.search(r'/layout/grid/?$', link):
                            link = link + '/layout/grid'
                    download_image_gallery(link)
                else:
                    download_image(link)


def page_get_next_page(webpage):
    '''
    # Find the link to the next page, if it exists
    # If it does, download and return the page
    # Otherwise, return None explicitly
    '''
    global args
    urls = webpage.find_all('a')
    log.d('found %s urls' % len(urls))
    log.d(args.next_page_regex.format(args.user_name))
    for url in urls:
        next_page = re.search(
            args.next_page_regex.format(args.user_name),
            str(url))
        if next_page and not next_page == []:
            log.d('matches found for %s' % url)
            log.d('returning early')
            return get_web_page(next_page.expand(r'\1').replace('amp;', ''))
        else:
            log.d('no matches for %s' % url)


def action_download_submitted_images():
    global args
    # Download all images from the first page
    user_submitted = get_submitted_page()
    get_all_images(user_submitted)

    if args.recursive:  # misnomer
        while True:  # Loop until we can't find a next page link
            log.d('looking for next page...')
            user_submitted = page_get_next_page(user_submitted)
            if user_submitted is None:
                log.d('no next page')
                break

            get_all_images(user_submitted)


def action_download_imgur_gallery():
    global args
    if not re.match(
            r"^(?:a/|gallery/|)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            args.gallery):
        raise ArgumentException(
            "GALLERY should be a valid Imgur URL without 'imgur.com/'")

    url = 'https://imgur.com/' + args.gallery

    if args.imgur_force_grid:
        if not re.search(r'/layout/grid/?$', url):
            url = url + '/layout/grid'

    if args.force_album:
        if re.search(r'/gallery/', url):
            url = url.replace('/gallery/', '/a/')

    download_image_gallery(url)


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
    global parser
    # handle gallery args
    ua = str(arg)
    if not re.match(
            r"^(?:a/|gallery/|)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            arg):
        parser.error('invalid GALLERY')
    return ua


def is_uname(arg):
    global parser
    # handle username args
    ua = str(arg)
    if re.match(
            r"^(?:a/|gallery/)(?:[a-zA-Z0-9]{5}|[a-zA-Z0-9]{7})$",
            arg):
        parser.error('invalid USERNAME')
    return ua


# -----------------------------------------------------------------------------


def get_args():
    global parser
    parser = ArgumentParser(
        description='SPD: Download every image a redditor ' +
                    'has submitted (ever)',
        usage='%(prog)s [options] ( USERNAME | -g GALLERY )',
        formatter_class=ArgumentDefaultsHelpFormatter)

    positional_group = parser.add_mutually_exclusive_group(required=True)

    adv_arg_group = parser.add_argument_group(
        title='advanced arguments',
        description='These options change how SPD reads a webpage. ' +
        'They require intimate knowledge of the pages you are searching. ' +
        'Use caution with these!')

    # positional args
    positional_group.add_argument(
        'user_name',
        type=is_uname,
        nargs='?',
        help='The name of the redditor whose images ' +
             'you\'d like to download')

    positional_group.add_argument(
        '-g', '--gallery',
        type=is_gal,
        help='The URL to the Imgur gallery you\'d like to download, ' +
             'minus \'https://imgur.com/\'')

    # optional args
    parser.add_argument(
        '-a', '--force-album',
        help='Replace "/gallery/" with "/a/". ' +
             'Can be useful when galleries do not have a grid layout',
        action='store_true',
        default=False)

    parser.add_argument(
        '-d',
        type=str,
        help='The directory to save the images in. ' +
             '<username> is appended to this value.',
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

    # advanced args
    adv_arg_group.add_argument(
        '--gallery-regex',
        type=str,
        help='Sets a custom regex for testing if a link is a gallery.',
        default=r'https://(?:imgur\.com/|gfycat\.com/)',
        metavar='REGEX')

    adv_arg_group.add_argument(
        '--imgur-gallery-image-regex',
        type=str,
        help='Sets a custom regex for finding all images in an Imgur gallery. ' +
             '(original layout)',
        default='//(i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|' +
                '[a-zA-Z0-9]{5})\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?)',
        metavar='REGEX')

    adv_arg_group.add_argument(
        '--imgur-grid-image-regex',
        type=str,
        help='Sets a custom regex for finding all images in an Imgur gallery. ' +
             '(grid layout)',
        default='//(i\\.imgur\\.com/[a-zA-Z0-9]{8}' +
                '\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?)',
        metavar='REGEX')

    adv_arg_group.add_argument(
        '--image-link-regex',
        type=str,
        help='Sets a custom regex for finding all images on the user\'s ' +
             'submitted page.',
        default='(https?://(?:gfycat\\.com/[a-zA-Z]+?|' +
                '(?:fat|giant|zippy)\\.gfycat\\.com/[a-zA-Z]+?\\.webm|' +
                'giant\\.gfycat\\.com/[a-zA-Z]+?\\.gif|' +
                'imgur\\.com/(?:[a-zA-Z0-9]{7}|[a-zA-Z0-9]{5})|' +
                'imgur\\.com/a/[a-zA-Z0-9]{5}|' +
                'imgur\\.com/gallery/[a-zA-Z0-9]{5}|' +
                'i\\.imgur\\.com/(?:[a-zA-Z0-9]{7}|[a-zA-Z0-9]{5})' +
                '\\.(?:[a-z]{3,4})(?:\\?[0-9]+?)?))',
        metavar='REGEX')

    adv_arg_group.add_argument(
        '--next-page-regex',
        type=str,
        help='Sets the regex used to find the URL for the next page. ' +
             'The first \'{!s}\' is replaced by the user\'s name. ' +
             'All other {\'s and }\'s should be doubled up. ' +
             'See https://docs.python.org/3/library/string.html#formatspec',
        default='(https?://www\\.reddit\\.com/user/{!s}' +
                '/submitted/\\?count=[0-9]{{2,4}}&amp;after=t[0-9]_[a-z0-9]{{6}})',
        metavar='REGEX')

    adv_arg_group.add_argument(
        '--submitted-page-pattern',
        type=str,
        help='Sets the pattern used to construct the link to the user\'s ' +
             'submitted page. ' +
             'The first \'{!s}\' is replaced by the user\'s name.',
        default='https://www.reddit.com/user/{!s}/submitted/',
        metavar='PATTERN')

    return parser.parse_args()


# -----------------------------------------------------------------------------


def main():
    global args
    args = get_args()

    if args.user_name:
        download_directory = os.path.expanduser(args.directory +
                                                '/' + args.user_name)
    elif args.gallery:
        download_directory = os.path.expanduser(args.directory +
                                                '/gallery/' + args.gallery)

    # make sure the download directory exists, then change to it
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)
    os.chdir(download_directory)

    if args.user_name:
        action_download_submitted_images()
    elif args.gallery:
        action_download_imgur_gallery()


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        pass
    except:
        log.c('Uncaught Exception:')
        log.c(format_exc())
