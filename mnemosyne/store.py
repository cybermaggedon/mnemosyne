
import logging
import subprocess
import os
import time

logger = logging.getLogger("mnemosyne")

class EncryptedStore:

    def __init__(self, file, keyfile):
        self.file = file
        self.volume = "mnemosyne-volume"
        self.device = "/dev/mapper/" + self.volume
        self.keyfile = keyfile

    def device_path(self):
        return self.device

    @staticmethod
    def init(file, size, keyfile):

        logger.info("Create encrypted store file...")

        proc = subprocess.run(
            [
                "truncate", "-s", f"{size}G", file
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Backup store creation failed")

        logger.info("Setup encryption key...")

        proc = subprocess.run(
            [
                "cryptsetup", "--batch-mode",
                "luksFormat", file, keyfile
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Backup store creation failed")

    def is_open(self):

        return os.path.exists(self.device)

    def open(self):

        logger.info("Opening encrypted store...")

        proc = subprocess.run(
            [
                "cryptsetup", "open", self.file, self.volume,
                "--key-file", self.keyfile
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Encrypted store access failed")

    def close(self):

        logger.info("Closing encrypted store...")

        proc = subprocess.run(
            [
                "cryptsetup", "close", self.volume
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Encrypted store access failed")

    def __enter__(self):

        if self.is_open():
            logger.info("Encrypted store already open, closing...")
            try:
                self.retry(self.close)
            except:
                raise RuntimeError("Could not unmount remote filesystem")
            logger.info("Closed successfully")

        self.open()

        return self

    def retry(self, fn, args=(), retries=5, delay=3):

        while True:

            try:
                fn(*args)
            except Exception as e:
                logger.info("Failed, retrying...")
                time.sleep(delay)

                retries -= 1

                if retries <= 0:
                    logger.info("Retries failed, giving up")
                    raise e

                continue

            break

    def __exit__(self, *args):

        self.retry(self.close)
        logger.info("Encrypted store closed successfully")

