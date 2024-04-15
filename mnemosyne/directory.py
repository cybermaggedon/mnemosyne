
import logging
import subprocess
import os
import time

logger = logging.getLogger("mnemosyne")

class DirectoryBackup:

    @staticmethod
    def run(key, directory, mnt, strategy):

        last_path = mnt + "/" + key + ".last"

        if os.path.exists(last_path):
            last_backup = int(open(last_path).read())
        else:
            last_backup = 0

        now = time.time()
        age = now - last_backup

        # Rotate period is in hours
        rotate_period = strategy.rotate * 3600

        if age >= rotate_period:
            rotate = True
        else:
            rotate = False

        if rotate:

            logger.info(f"Rotating backup directories for {key}...")

            for stage in range(strategy.stages - 1, 0, -1):

                cur_target = mnt + "/" + key + "." + str(stage - 1)
                prior_target = mnt + "/" + key + "." + str(stage)

                if os.path.exists(cur_target):

                    if os.path.exists(prior_target):
                        DirectoryBackup.delete_subvolume(prior_target)

                    DirectoryBackup.snapshot(
                        cur_target, prior_target
                    )

            logger.info("Rotation successful")

            logger.info("Creating new subvolume...")

            target = mnt + "/" + key + "." + str(0)

            if not os.path.exists(cur_target):
                DirectoryBackup.create_subvolume(target)

            now = int(time.time())
            with open(last_path, "w") as lf:
                lf.write(f"{now}")

            DirectoryBackup.rsync(directory, target, delete=True)

        else:

            logger.info(f"Not rotating backup directories for {key}")

            target = mnt + "/" + key + "." + str(0)

            DirectoryBackup.rsync(directory, target, delete=False)

    @staticmethod
    def rsync(src, dest, delete=False):

        logger.info(f"Syncing directory {src}...")

        if delete:
            proc = subprocess.run(
                [
                    "rsync", "-av", src + "/", dest + "/",
                ]
            )
        else:
            proc = subprocess.run(
                [
                    "rsync", "--delete", "-av", src + "/", dest + "/",
                ]
            )

        if proc.returncode != 0:
            raise RuntimeError(
                "Directory sync failed"
            )

        logger.info("Sync complete")

    @staticmethod
    def delete_subvolume(subvol):

        proc = subprocess.run(
            [
                "btrfs", "subvolume", "delete", subvol,
            ]
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "Removal of subvolume"
            )

    @staticmethod
    def snapshot(src, dest):

        proc = subprocess.run(
            [
                "btrfs", "subvolume", "snapshot", src, dest,
            ]
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "Subvolume snapshot"
            )

    @staticmethod
    def create_subvolume(subvol):

        proc = subprocess.run(
            [
                "btrfs", "subvolume", "create", subvol,
            ]
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "Creation of subvolume"
            )
