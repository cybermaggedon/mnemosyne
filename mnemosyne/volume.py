
import logging
import subprocess
import os
import time
import sys

logger = logging.getLogger("mnemosyne")

class Volume:

    def __init__(self, device):
        self.device = device
        self.mnt = "/tmp/mnemosyne-volume"

    @staticmethod
    def init(file):

        logger.info("Initialise volume...")

        proc = subprocess.run(
            [
                "mkfs.btrfs", "-f", file
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Backup store creation failed")

    def is_mounted(self):
        with open('/proc/mounts','r') as f:
            mount_points = [line.split()[1] for line in f.readlines()]
        return self.mnt in mount_points

    def mount(self):

        logger.info("Mounting volume...")

        proc = subprocess.run(
            [
                "mount", self.device, self.mnt,
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Remote FS mount failed")

    def unmount(self):

        logger.info("Unmounting volume...")

        proc = subprocess.run(
            [
                "umount", self.mnt
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Remote FS unmount failed")

    def __enter__(self):

        if self.is_mounted():
            logger.info("Already mounted, unmounting...")
            try:
                self.retry(self.unmount)
            except:
                raise RuntimeError("Could not unmount volume")
            logger.info("Unmounted successfully")

        try:
            os.makedirs(self.mnt, exist_ok=True)
        except:
            raise RuntimeError("Could not create '" + self.mnt + "'")

        self.mount()

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

    def mount_point(self):
        return self.mnt

    def __exit__(self, *args):
    
        self.retry(self.unmount)
        logger.info("Remote FS unmounted successfully")

