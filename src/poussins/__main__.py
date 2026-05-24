# Entrypoint for `python -m poussins`.
# Sets up logger and global error handler.
from .cli.main import main

if __name__ == "__main__":
    main()
