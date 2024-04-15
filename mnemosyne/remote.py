
import logging
import subprocess
import os
import time

logger = logging.getLogger("mnemosyne")

class RemoteFS:

    def __init__(self, remote):
        self.remote = remote
        self.mnt = "/tmp/mnemosyne-remote"

    def is_mounted(self):
        with open('/proc/mounts','r') as f:
            mount_points = [line.split()[1] for line in f.readlines()]
        return self.mnt in mount_points

    def mount(self):

        logger.info("Mounting remote FS...")

        proc = subprocess.run(
            [
                "mount.cifs", self.remote.volume, self.mnt,
                "-o", f"user={self.remote.username},pass={self.remote.password}"
            ]
        )
        
        if proc.returncode != 0:
            raise RuntimeError("Remote FS mount failed")

    def unmount(self):

        logger.info("Unmounting remote FS...")

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
#                self.unmount()
            except:
                raise RuntimeError("Could not unmount remote filesystem")
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

