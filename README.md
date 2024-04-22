
# `mnemosyne`

This is a simple, opinionated backup system which works well with a Linux
system backing up to a remote NAS system.  I'm using a Synologic. If this
code is useful to you, great.

Data on the NAS is encrypted using a key file, so loss of NAS to theft is
not enough for compromise of private data.  Obviously, protection of the key
by you is important.

This is a Python package providing a single command line utility which covers
everything to do with backup.  Restoration from backup is not automated, so
you need to know how to mount the backup to fetch files in case you need
to recover something.

## How it works

This is a Python package providing a command line utility which takes
care of everything.  A configuration file defines everything, including
security parameters.  The script executes basic Linux command line
utilities to do the backup, including executing the rsync command.

A backup consists of the following steps:
- A remote filesystem is mount from the NAS onto the Linux 'client'.
  The remote mount can be either:
  - a CIFS filesystem for NAS systems which export a CIFS/SMB filesystem, or
  - a block device.  This is useful for backing up to a SAN / iSCSI device.
- An encrypted image contained within that remote filesystem is opened using
  Linux LUKS.  This ensures that data written to that image is encrypted, and
  not accessible without the encryption key.
- A BTRFS filesystem contained in that encrypted image is mounted.  BTRFS
  is chosen for the ability to snapshot subvolumes.  This allows capturing
  data at a point in time.
- Periodically, the directory to which data is written on the backup
  filesystem has a subvolume rotation to keep a number of major 'point in
  time' backups.
- The rsync command is used to transfer data from the Linux 'client' to the
  remote backup by copying to the BTRFS filesystem.
- At the end, everything is unmounted.

## Design decisions

There are number of design trade-offs in backup systems.

| Design goal | Rationale | Mnemosyne approach |
| ------------ | --------------------------- | ------------------------- |
| Speed of transfer | To make transfer of large amounts of data as efficent as possible, it is useful to use systems which efficiently stream blocks of data from the filesystem as efficiently as possible, e.g. using the UNIX/Linux dump command | Have traded other design features as more important |
| Recovery of single files or directories | Backing data up is one thing.  Need to consider the efficiency of restoring data | Data is rsync'd into directories, so you can find the data to be restored with relative ease.  There is a whole heap of manual work needed to restore a complete system from such a backup |
| Low cost of incremental backup | I want to backup often, so don't want a huge cost for taking the decison to backup | Backups are always incremental with reference to everything back'd up, so this minimises data transfer |
| Need to be able to restore with the minimum amount of tech, given that recovery may need to take place after complete loss of system | The system backups & restores using simple standard Linux commands |
| Encryption of data | Securing information is hard.  I don't want encryption keys to be obtained easily by e.g. storing keys in clear on the NAS and stealing the NAS | The encryption key is not stored on the NAS.  It is stored in clear on the client.  Loss of NAS does not mean loss of encryption key |

## Example configuration files

| Configuration path | Meaning |
| ------------------ | ------- |
| remote.type | Type of remote filesystem, cifs or block |
| remote.volume | For CIFS, specifies the remote volume name.  This has backslash characters in which need to be double'd (quoted) in JSON |
| remote.username | For CIFS, specifies the remote volume username credential |
| remote.password | For CIFS, specifies the remote volume password credential |
| remote.block | For Block filesystem, specifies the block device to mount.  For best results, find out the UUID of the filesystem and use form UUID=xxx |
| store.name | The name of the encrypted backup image.  Doesn't matter what you call it |
| store.size | The initial size of the backup image.  This value affects the initialisation, once it is set up changing this value does nothing |
| store.keyfile | A file containing an encryption key for the store |
| strategy.stages | The number of snapshots to keep.  The volume is periodically rotated to keep old data, this is the number of rotation snapshots to keep |
| strategy.rotate | The period in hours on which snapshots are rotated |
| local.directories[].key | Prefix used to name subvolume directories |
| local.directories[].directory | Directory name which is to be backed up |

### CIFS

```
{
    "remote": {
	"type": "cifs",
	"volume": "\\\\synologic.local\\volumename",
	"username": "user123",
	"password": "PASSWORD-GOES-HERE"
    },
    "store": {
	"name": "backup.btrfs",
	"size": 2200,
	"keyfile": "/usr/local/etc/mnemosyne/key"
    },
    "strategy": {
	"stages": 8,
	"rotate": 168
    },
    "local": {
	"directories": [
	    {
		"key": "etc",
		"directory": "/etc"
	    },
	    {
		"key": "home",
		"directory": "/home"
	    }
	]
    }
}
```

### iSCSI

```
{
    "remote": {
	"type": "block",
	"device": "UUID=441c6328-515d-45c7-84d9-bffb3097fbac"
    },
    "store": {
	"name": "backup.btrfs",
	"size": 2200,
	"keyfile": "/usr/local/etc/mnemosyne/key"
    },
    "strategy": {
	"stages": 8,
	"rotate": 168
    },
    "local": {
	"directories": [
	    {
		"key": "etc",
		"directory": "/etc"
	    },
	    {
		"key": "home",
		"directory": "/home"
	    }
	]
    }
}
```

## Options

```
usage: mnemosyne [-h] [--init-store] [--init-key] [--backup] [--mount]
                 [--verify-environment] [--config CONFIG]

Backup to remote filesystem

options:
  -h, --help            show this help message and exit
  --init-store          Initialise encrypted backup store
  --init-key            Initialise secure backup key
  --backup              Run a backup cycle
  --mount               Mount backup target
  --verify-environment  Verify environment
  --config CONFIG, -c CONFIG
                        Backup configuration file
```

## Setting it up

- Create the configuration file
- Run `mnemosyne --init-key` to create a random encryption key.
- *Store the encryption key somewhere safe!*
- Run `mnemosyne --init-store` to mount the remote filesystem and initialise the encrypted store
- Run `mnemosyne --backup` every time you want to run a backup.  The first backup will be a full transfer, subsequent backups will be quicker.

