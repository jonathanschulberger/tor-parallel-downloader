# tor-parallel-downloader

## Summary
This tool enables you to map an http file listing (Apache/NGINX) and either create a directory listing or download the entire directory tree.

## Requirements
- Linux/Unix
- Python 3
- Docker
- enough disk space to hold files (if downloading)

## Setup (Linux/Unix)
1) Clone repository: git clone git@github.com:jonathanschulberger/tor-parallel-downloader.git
2) Enter repository folder: cd tor-parallel-downloader
3) Create python virtual environment: python -m venv .venv
4) Activate virtual environment: source ./.venv/bin/activate
5) Install python requirements: pip install -r requirements.txt

## Usage
You can either:
- download the entirety of an http file listing: python tor-parallel-downloader.py
- create a file listing from a root address: python tor-parallel-downloader.py -a map
- download a list of files: python tor-parallel-downloader.py -a get -f <file-list>

### File List
Format is as follows:
<file-link-1>
<file-link-2>
...
