# tor-parallel-downloader

## Summary
This tool enables you to map an http file listing (Apache/NGINX) and either create a directory listing or download the entire directory tree.

## Requirements
- Linux/Unix
- Git
- Python 3
- Docker
- enough disk space to store files (if downloading)

## Setup (Linux/Unix)
1) Clone repository

    `git clone git@github.com:jonathanschulberger/tor-parallel-downloader.git`
2) Enter repository folder

    `cd tor-parallel-downloader`
3) Create python virtual environment

    `python -m venv .venv`
4) Activate virtual environment

    `source ./.venv/bin/activate`
5) Install python requirements

    `pip install -r requirements.txt`

## Usage (Linux/Unix)
You can either:
- download the entirety of an http file listing

   `python tor-parallel-downloader.py -u <url> [-d DOWNLOAD_ROOT]`
- create a file listing from a root address

   `python tor-parallel-downloader.py -u <url> -a map [-d DESTINATION_DIRECTORY]`
- download a list of files

   `python tor-parallel-downloader.py -a get -f <file-list> [-d DOWNLOAD_ROOT]`
- resume download

   `python tor-parallel-downloader.py -a resume -f <file-list>`

### File List
Minimum format is as follows:
```
<file-link-1>
<file-link-2>
...
```

## FAQ
- If you stop this application with `CTRL+C`, you will need to go to `Docker Desktop -> Containers` and click the `stop` button next to each container that starts with `tor-proxy-`.
