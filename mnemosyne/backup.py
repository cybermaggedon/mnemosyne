
import json
import os
import time
import logging
import shutil

from .types import *
from .remote import RemoteFS
from .store import EncryptedStore
from .volume import Volume
from .directory import DirectoryBackup

logger = logging.getLogger("mnemosyne")

class Backup:

    def __init__(self, config):

        try:
            with open(config) as f:
                self.config = json.load(f)
        except Exception as e:
            raise RuntimeError("Parsing config file: " + str(e))

        try:
            self.remote = Remote.parse(self.config["remote"])
        except Exception as e:
            raise RuntimeError("Parsing 'remote' config: " + str(e))

        try:
            self.store = Store(**self.config["store"])
        except Exception as e:
            raise RuntimeError("Parsing 'store' config: " + str(e))

        try:
            self.strategy = Strategy(**self.config["strategy"])
        except Exception as e:
            raise RuntimeError("Parsing 'strategy' config: " + str(e))

        try:
            self.directories = [
                Directory(**v)
                for v in self.config["local"]["directories"]
            ]
        except Exception as e:
            raise RuntimeError("Parsing 'local' config: " + str(e))
            
    def verify(self):

        failed = False

        uid = os.getuid()

        if uid == 0:
            logger.info(" \u2713 Running as root")
        else:
            logger.info(" \u274c Not running as root")
            failed = True

        if shutil.which("cryptsetup"):
            logger.info(" \u2713 cryptsetup available")
        else:
            logger.info(" \u274c cryptsetup not available")
            failed = True
            
        if shutil.which("btrfs"):
            logger.info(" \u2713 btrfs available")
        else:
            logger.info(" \u274c btrfs not available")
            failed = True
            
        if shutil.which("mount.cifs"):
            logger.info(" \u2713 mount.cifs available")
        else:
            logger.info(" \u274c mount.cifs not available")
            failed = True
            
        if shutil.which("mount"):
            logger.info(" \u2713 mount available")
        else:
            logger.info(" \u274c mount not available")
            failed = True
            
        if failed:
            logger.error(" Verification has failed")
            raise RuntimeError("Verification has failed")

        logger.info(" Verified successfully.")

    def init(self):

        with RemoteFS(self.remote) as fs:

            encrypted_store = fs.mount_point() + "/" + self.store.name

            if os.path.exists(encrypted_store):

                logger.error(f"Store '{encrypted_store}' exists!")
                logger.error(f"Refusing to initialise store")
                raise RuntimeError("Store file already exists on remote disk")

            EncryptedStore.init(
                encrypted_store, self.store.size, self.store.keyfile
            )

            with EncryptedStore(encrypted_store, self.store.keyfile) as s:

                Volume.init(s.device_path())

        logger.info("Initialisation completed successfully.")

    def backup(self):

        with RemoteFS(self.remote) as fs:

            encrypted_store = fs.mount_point() + "/" + self.store.name

            with EncryptedStore(encrypted_store, self.store.keyfile) as s:

                with Volume(s.device_path()) as vol:

                    for direc in self.directories:

                        DirectoryBackup.run(
                            direc.key, direc.directory, vol.mount_point(),
                            self.strategy
                        )

        logger.info("Backup cycle completed successfully.")

    def mount(self):

        logger.info("Mounting backup target...")

        with RemoteFS(self.remote) as fs:

            encrypted_store = fs.mount_point() + "/" + self.store.name

            with EncryptedStore(encrypted_store, self.store.keyfile) as s:

                with Volume(s.device_path()) as vol:

                    print("*** Backup target is mounted on", vol.mount_point())
                    print("*** Press Ctrl-C to unmount")

                    while True:
                        time.sleep(10)

        logger.info("Unmounted")

