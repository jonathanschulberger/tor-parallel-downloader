import os

from util.file_io import write_file_list, read_file_list
from util.proxied_tasks import download_files, get_file_listing


FILE_LISTING_FILENAME = 'file_listing.csv'


def map_and_download():
    # create time.time() folder as <root>
    # get file listing
    # write to file in <root>
    # download files info <root>/files/
    pass

def resume(download_root: str):
    download_list(os.path.join(download_root), FILE_LISTING_FILENAME)

def download_list(file_listing: str, download_root: str = None):
    file_list = read_file_list(file_listing)
    download_files(file_list, download_root=download_root, number_of_proxies=file_list.qsize(), debug=True)

def create_map(base_url: str):
    files = get_file_listing(base_url, debug=True)
    write_file_list(files)

    # report findings
    total_bytes = sum([file['metadata']['size'] for file in files])
    print(f'[INFO] found {len(files)} files totaling {total_bytes} bytes (~{total_bytes // 1073741824} GB)')


if __name__ == '__main__':
    pass
    # argparse
    # -a - action - map,get,resume,<absent>
    # -f - file/folder - <path> - only applicable when [-a get|resume]
    # -u - url - <url> - only required/applicable when [-a map|<absent>]
    # call relevant method
