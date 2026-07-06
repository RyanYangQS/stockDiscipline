import argparse

from app.config import DEFAULT_HOST, DEFAULT_PORT
from app.server import run


def main():
    parser = argparse.ArgumentParser(description="Run Stock Discipline web server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()

