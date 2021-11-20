from bs4 import BeautifulSoup
import csv
import os
import queue
import time
import urllib.parse as url_parser

FILE_LISTING_FILENAME = 'file_listing.csv'


def read_file_list(file_listing: str, debug: bool = False) -> queue.SimpleQueue:
    files_to_download = queue.SimpleQueue()
    with open(file_listing, mode='r') as file_list_fd:
        for line in file_list_fd:
            line = line.strip()
            if line:
                files_to_download.put(line)
    
    if debug:
        print(f"[INFO] read {files_to_download.qsize()} from file list")

    return files_to_download


def write_file_list(files: list, output_path: str = None, file_prefix: str = '', debug: bool = False):
    # write file paths to csv
    if not output_path:
        output_path = os.path.join('downloads', str(int(time.time())), FILE_LISTING_FILENAME)
    
    with open(f'{output_path}.csv', 'w') as outfile:
        csvwriter = csv.writer(outfile)
        csvwriter.writerow(['timestamp', 'size (bytes)', 'url'])
        for file in files:
            try:
                timestamp = file['metadata']['last_modified']
                file_size = int(file['metadata']['size'])
                csvwriter.writerow([
                    timestamp,
                    file_size,
                    url_parser.unquote_plus(file['url'][file['url'].index(file_prefix) + len(file_prefix):])])
            except Exception as e:
                print(f'[ERROR] could not write: {file}\n\t{str(e)}')
    if debug:
        print(f"[INFO] file list written to '{output_path}'")
