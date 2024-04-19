
import argparse
import logging
import sys
import signal
import os

from .backup import Backup

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("mnemosyne")
logger.setLevel(logging.INFO)


def run():

    parser = argparse.ArgumentParser(
        prog="mnemosyne", description="Backup to remote filesystem"
    )

    parser.add_argument("--init-store", 
                        action="store_const", dest='action', const='init-store',
                        help="Initialise encrypted backup store")

    parser.add_argument("--init-key", 
                        action="store_const", dest='action', const='init-key',
                        help="Initialise secure backup key")

    parser.add_argument("--backup", 
                        action="store_const", dest='action', const='backup',
                        help="Run a backup cycle")

    parser.add_argument("--mount", 
                        action="store_const", dest='action', const='mount',
                        help="Mount backup target")

    parser.add_argument("--verify-environment", 
                        action="store_const", dest='action', const='verify',
                        help="Verify environment")

    parser.add_argument(
        "--config", '-c', default="/usr/local/etc/mnemosyne/config.json",
        action="store", 
        help="Backup configuration file"
    )

    try:

        logger.info("Starting...")

        args = parser.parse_args()

        backup = Backup(config=args.config)

        if args.action == "verify":
            logger.info("Verifying environment...")
            backup.verify()
            sys.exit(0)

        if args.action == "init-store":
            logger.info("Initialising backup store...")
            backup.init_store()
            sys.exit(0)

        if args.action == "init-key":
            logger.info("Initialising secure key...")
            backup.init_key()
            sys.exit(0)

        if args.action == "backup":
            logger.info("Running backup...")
            backup.backup()
            sys.exit(0)

        if args.action == "mount":
            logger.info("Mounting backup target...")
            backup.mount()
            sys.exit(0)

        logger.error("You need to specify an action to take")
        sys.exit(1)

    except Exception as e:

        print("Exception:", e)

def shutdown_handler(signal, frame):
    logger.info("Signal received, shutting down.")
    logger.info("Exiting.")
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == "__main__":
    run()

