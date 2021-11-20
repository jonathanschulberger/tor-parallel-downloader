import os
import queue
import requests
import subprocess
import threading
import time

DOCKER_IMAGE = "jschulberger/tor:0.4.6"


def create_proxy(port: int, names: queue.SimpleQueue):
    """
    Create Tor proxy.

    Spawn Tor proxy in docker container on localhost and allow access via <port>.

    Parameters:
    port (int): Port on localhost that proxy is accessible at.
    names (queue.SimpleQueue): Hostnames of Tor-proxy docker containers.

    Returns:
    """
    name = "tor-proxy-{}".format(port)
    subprocess.Popen("docker run -d --rm --name \"{}\" -p {}:9050 --mount type=bind,source=\"{}\",target=/home/tor/.torrc,readonly {} ".format(name, port, os.path.join(os.getcwd(), "torrc", DOCKER_IMAGE)), shell=True, stdout=subprocess.PIPE)
    while True:
        try:
            # attempt TOR request via proxy
            requests.get(
                    'https://check.torproject.org/',
                    proxies={
                        'http':'socks5://127.0.0.1:{}'.format(port),
                        'https':'socks5://127.0.0.1:{}'.format(port)
                    },
                    timeout=10
                ).text
            # request succeeded, report success
            names.put(name)
            return
        except:
            # docker container must not be up yet, wait for 1 second
            print('Waiting for {}...'.format(name))
            time.sleep(5)

def create_proxies(start_port: int, count: int):
    """
    Create <count> Tor proxies

    Spawn <count> Tor proxies via create_proxy method.

    Parameters:
    start_port (int): Port on localhost that proxy #1 is available at.
    count (int): Number of proxies to spawn.

    Returns:
    queue.SimpleQueue: Hostnames of Tor-proxy docker containers.
    """
    names = queue.SimpleQueue()
    threads = [threading.Thread(target=create_proxy, args=(port, names,)) for port in range(start_port, start_port + count)]
    for thr in threads:
        thr.start()
    while any([thread.is_alive() for thread in threads]):
        pass
    for thr in threads:
        thr.join()
    return names

def destroy_proxy(container_name: str):
    """
    Remove docker container with name <container_name>.

    Stop docker container with name <container_name>.
    Once stopped, the docker container will be deleted due to the initial --rm argument.

    Parameters:
    container_name (str): Name of docker container to remove.

    Returns:
    """
    subprocess.Popen(f"docker stop {container_name}", shell=True, stdout=subprocess.PIPE)
    return container_name

def destroy_proxies(container_names: queue.SimpleQueue):
    """
    Remove all proxies specified in <container_names>.

    Apply <destroy_proxy> function to all container names in <container_names>.

    Parameters:
    container_names (queue.SimpleQueue): Docker container names of all Tor proxies on host.

    Returns:
    """
    while not container_names.empty():
        destroy_proxy(container_names.get())
