import argparse
import os
import time

from util.file_io import write_file_list, read_file_list
from util.proxied_tasks import download, download_files, get_file_listing


def map_and_download(url: str, download_root: str = None, debug: bool = False):
    file_list_location = create_file_list(url, download_root, debug=debug)
    download_file_list(file_list_location, os.path.dirname(file_list_location), debug=debug)


def resume(file_list: str, debug: bool = False):
    download_file_list(file_list, os.path.dirname(file_list), False, debug=debug)


def download_file_list(file_listing: str, download_root: str = None, clear_existing: bool = True, debug: bool = False):
    file_list = read_file_list(file_listing, debug=debug)
    download_files(file_list, download_root=download_root, number_of_proxies=file_list.qsize(), clear_existing=clear_existing, debug=debug)


def create_file_list(base_url: str, download_root: str = None, debug: bool = False):
    file_list = get_file_listing(base_url, debug=debug)
    return write_file_list(file_list, download_root, debug=debug)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", dest="action", choices=["get", "map", "resume"],
        help="action to perform\n\t" +
             "get: ONLY get files in file listing\n\t" +
             "map: ONLY get file listing\n\t" +
             "resume: resume download\n\t" +
             "<absent>: recursively explore URL and download")
    parser.add_argument("-d", dest="download_root",
                        help="Download root. Required when action is 'resume'")
    parser.add_argument("-f", dest="file_list",
                        help="Path to file list. " +
                        "Required when action is either 'get' or 'resume'")
    parser.add_argument("-u", dest="url",
                        help="Target URL. Required when action is either 'map' or <absent>")
    parser.add_argument("--debug", dest="debug", help="max output verbosity",
                        action="store_true")
    args = parser.parse_args()

    if args.action in ["get", "resume"]:
        if not args.target_path:
            parser.print_help()
            raise RuntimeError("'-f' required if action is 'get' or 'resume'")
        if args.action == "resume" and not args.download_root:
            parser.print_help()
            raise RuntimeError("'-d' is required when action is 'resume'")

    if args.action in ["map", None]:
        if not args.url:
            parser.print_help()
            raise RuntimeError("'-u' required if action is 'get' or <absent>")

    return args, parser


if __name__ == '__main__':
    try:
        args, parser = parse_arguments()
        
        if not args.action:
            map_and_download(args.url, args.download_root, debug=args.debug)

        if args.action == 'map':
            create_file_list(args.url, debug=args.debug)

        if args.action == 'get':
            download_file_list(args.file_list, args.download_root, debug=args.debug)

        if args.action == 'resume':
            resume(args.download_root, debug=args.debug)
    except Exception as exc:
        print(str(exc))

# resume will be broken by download in proxied_tasks because it clears file before downloading
