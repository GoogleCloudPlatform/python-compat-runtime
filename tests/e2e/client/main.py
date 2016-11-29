import argparse
import sys

import requests


def main(url):
    response = requests.get(url + 'refresh')
    if response.status_code != 200:
        print(response.status_code)
        print(response.headers)
        print(response.text)
        sys.exit(1)

    response = requests.get(url + 'test')

    print(response.text)

    if response.status_code != 200:
        print(response)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    main(args.url)
