from bs4 import BeautifulSoup
import queue
import os
import pathlib
import queue
import re
import requests
import threading
import time
import urllib.parse as url_parser

from util.file_io import write_file_list, FILE_LISTING_FILENAME
from util.tor_proxy import create_proxies, destroy_proxies


def query(url: str, proxy_port: int, folders: queue.SimpleQueue, files: queue.SimpleQueue, debug: bool = False):
    if debug:
        print(f"[INFO] [{proxy_port}] querying '{url}'")

    # setup request
    req_session = requests.session()
    req_session.proxies = {}
    req_session.proxies['http'] = f"socks5h://localhost:{proxy_port}"
    req_session.proxies['https'] = f"socks5h://localhost:{proxy_port}"

    # some servers don't allow requests without valid headers like the ones below
    heads = {}
    heads['User-agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
    heads['Content-type'] = "application/json"

    # use request session to retrieve desired page
    page = None
    while not page:
        try:
            page = req_session.get(url, headers=heads, timeout=30).text
            if debug:
                print(f'[INFO] [{proxy_port}] data received\n\t{page}')
        except Exception as e:
            print(f"[ERROR] [{proxy_port}] failed to get '{url}'\n\t{str(e)}\n\tadding back into queue")
            folders.put(url)
            return

    # gather href elements from retrieved page and parse out files and folders
    soup = BeautifulSoup(page, 'html.parser')
    for node in soup.find_all('a'):
        if not node.get('href') or node.get('href').startswith('#'):
            if debug:
                print(f"[WARN] [{proxy_port}] valid 'href' not found in element\n\t{str(node)}")
        elif node.get('href') in ['./', '../']:
            if debug:
                print(f"[WARN] [{proxy_port}] ignoring element with cyclical href\n\t{str(node)}")
            continue  # ignore current dir and parent dir links
        elif node.get('href').endswith('/'):
            if debug:
                print(f"[INFO] [{proxy_port}] recognized element as folder link\n\t{str(node)}")
            folders.put(url + node.get('href'))
        else:
            if debug:
                print(f"[INFO] [{proxy_port}] recognized element as file link\n\t{str(node)}")
            raw_metadata = requests.head(url + node.get('href'), timeout=30).headers
            files.put({
                'url': url + node.get('href'),
                'metadata': {
                    'last_modified': raw_metadata.get('Date', None),
                    'size': raw_metadata.get('Content-Length', None)
                }
            })

def get_file_listing(base_url: str, number_of_proxies: int = 8, start_port: int = 10050, debug: bool = False):
    # thread-safe objects for storing file listing and remaining folders
    files = queue.SimpleQueue()
    folders = queue.SimpleQueue()

    # create Tor proxies
    container_names = create_proxies(start_port, number_of_proxies)
    if debug:
        print(f"[INFO] successfully initialized {number_of_proxies} Tor proxies")

    # initialize <proxy_container>:<folder-exploration-thread> mapping
    proxy_request_map = {name: None for name in range(start_port, start_port + number_of_proxies)}

    # explore file/folder tree until all folders have been explored
    folders.put(base_url)
    while not folders.empty() or any(list(proxy_request_map.values())):
        for proxy, process in proxy_request_map.items():
            # if proxy is idling, assign folder to explore
            if process == None:
                if not folders.empty():
                    proxy_request_map[proxy] = threading.Thread(target=query, args=(folders.get(), proxy, folders, files, debug,))
                    proxy_request_map[proxy].start()
            # clear <proxy_container>:<folder-exploration-thread> mapping
            elif not process.is_alive():
                process.join()
                proxy_request_map[proxy] = None

        print(f'[INFO] {folders.qsize()} urls remaining', end='\r')
        time.sleep(0.25)

    print('\n[INFO] Scan completed!')

    # cleanup
    print('[INFO] detroying proxies ... ', end='')
    destroy_proxies(container_names)
    print('success')

    # return list of all file urls
    return [files.get() for _ in range(files.qsize())]

def download(url: str, download_root: str, proxy_port: int, clear_existing: bool = True, debug: bool = False):
    if debug:
        print(f"[INFO] [{proxy_port}] downloading '{url}'")

    # setup request
    req_session = requests.session()
    req_session.proxies = {}
    req_session.proxies['http'] = f"socks5h://localhost:{proxy_port}"
    req_session.proxies['https'] = f"socks5h://localhost:{proxy_port}"

    # some servers don't allow requests without valid headers like the ones below
    heads = {}
    heads['User-agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
    #heads['Content-type'] = "application/octet-stream"

    # setup download directory
    path_segments = re.match(r'^(?:http|https)\://[a-zA-Z0-9]+\.onion/(.+)$', url_parser.unquote_plus(url))
    if not path_segments.groups():
        raise RuntimeError(f"[ERROR] [{proxy_port}] cannot determine output location from '{url}'")
    file_destination = os.path.join(download_root, *path_segments.groups()[0].split('/'))
    folder_path = os.path.dirname(rf'{file_destination}')

    # ensure directory structure exists
    if debug:
        print(f"[INFO] [{proxy_port}] creating directory at '{folder_path}'")
    os.makedirs(folder_path, exist_ok=True)
    if clear_existing and os.path.exists(file_destination):
        if debug:
            print(f"[INFO] [{proxy_port}] removing existing file at '{file_destination}'")
        os.remove(file_destination)

    # use request session to retrieve file
    retries = 0
    max_retries = 360
    timeouts = (10, 10)
    content_size = 0
    bytes_downloaded = 0

    while retries <= max_retries:
        try:
            open_mode = 'wb'
            if debug:
                print(f"[INFO] [{proxy_port}] saving '{url}'\n\tto '{file_destination}'\n\t{retries} retries")
            if os.path.exists(file_destination):
                bytes_downloaded = pathlib.Path(file_destination).stat().st_size
                if debug:
                    print(f"[INFO] [{proxy_port}] already downloaded {bytes_downloaded} bytes of '{url}'")
                heads['Range'] = f'bytes={bytes_downloaded}-'
                open_mode = 'ab'
                if debug:
                    print(f"[INFO] [{proxy_port}] resuming download of '{url}'")
            with req_session.get(url, headers=heads, stream=True, timeout=timeouts) as dl:
                if debug:
                    print(f'[INFO] [{proxy_port}] get response\n\t{dl.__dict__}')
                dl.raise_for_status()
                if not content_size:
                    content_size = int(dl.headers['Content-Length'])
                    if debug:
                        print(f"[INFO] [{proxy_port}] '{url}' reported as {content_size} bytes")
                with open(file_destination, open_mode) as output_file:
                    for chunk in dl.iter_content(chunk_size=32*1024):
                        output_file.write(chunk)
                        retries = 0

            # ensure download has completed, else raise error
            bytes_downloaded = pathlib.Path(file_destination).stat().st_size
            if bytes_downloaded < content_size:
                raise RuntimeError(f"download timed out")
            return
        except Exception as e:
            if debug:
                print(f"[ERROR] [{proxy_port}] failed to get '{url}'\n\t{str(e)}")
            retries += 1
    print(f"[ERROR] [{proxy_port}] could not download '{url}'")
    if os.path.exists(file_destination):
        if debug:
            print(f"[INFO] [{proxy_port}] removing partially-downloaded file '{file_destination}'")
        os.remove(file_destination)

def download_files(file_list: queue.SimpleQueue, download_root: str = None, number_of_proxies: int = 16, start_port: int = 10050, clear_existing: bool = True, debug: bool = False):
    # only deploy as many proxies as we have to
    number_of_proxies = min(file_list.qsize(), number_of_proxies)
    
    # create Tor proxies
    container_names = create_proxies(start_port, number_of_proxies)
    if debug:
        print(f"[INFO] successfully initialized {number_of_proxies} Tor proxies")

    # initialize <proxy_container>:<folder-exploration-thread> mapping
    proxy_request_map = {name: None for name in range(start_port, start_port + number_of_proxies)}

    total_file_count = file_list.qsize()
    if not download_root:
        download_root = os.path.join('downloads', str(int(time.time())), 'files')
        if debug:
            print(f"[INFO] downloading to '{download_root}'")

    # place file listing
    os.makedirs(download_root, exist_ok=True)
    file_list_path = os.path.join(
        os.path.dirname(os.path.normpath(download_root)), FILE_LISTING_FILENAME)
    if not os.path.exists(file_list_path):
        write_file_list(list(file_list.queue), file_list_path, debug=debug)

    files_downloaded = 0
    while not file_list.empty() or any(list(proxy_request_map.values())):
        for proxy, process in proxy_request_map.items():
            # if proxy is idling, assign file to download
            if process == None:
                if not file_list.empty():
                    proxy_request_map[proxy] = threading.Thread(target=download, args=(file_list.get(), download_root, proxy, clear_existing, debug,))
                    proxy_request_map[proxy].start()
                # clear <proxy_container>:<folder-exploration-thread> mapping
                elif not process.is_alive():
                    process.join()
                    proxy_request_map[proxy] = None
                    files_downloaded += 1

        print(f'Download progress: {files_downloaded}/{total_file_count} ({100 * (files_downloaded // total_file_count)}%)', end='\r')
        time.sleep(1)

    if debug:
        print(f"[INFO] finished downloading files to '{download_root}'")

    # deconstruct proxies
    destroy_proxies(container_names)
