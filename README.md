
# `mnemosyne`

This is a simple, opinionated backup system which works well with remote
NAS systems for my use-cases.  If it's useful to you, great.

## Design decisions

There are number of design trade-offs in backup systems.

| Aspect | Rationale | Mnemosyne approach |
| ------------ | --------------------------- | ------------------------- |
| Speed of transfer | To make transfer of large amounts of data as efficent as possible, it is useful to use systems which efficiently stream blocks of data from the filesystem as efficiently as possible, e.g. using the UNIX/Linux dump command | Have traded other design features as more important |
| Recovery of single files or directories | Backing data up is one thing.  Need to consider the efficiency of restoring data | Data is rsync'd into directories, so you can find the data to be restored with relative ease.  There is a whole heap of manual work needed to restore a complete system from such a backup |
| Low cost of incremental backup | I want to backup often, so don't want a huge cost for taking the decison to backup | Backups are always incremental with reference to everything back'd up, so this minimises data transfer |
| Need to be able to restore with the minimum amount of tech, given that recovery may need to take place after complete loss of system | The system backups & restores using simple standard Linux commands |
| Encryption of data | Securing information is hard.  I don't want encryption keys to be obtained easily by e.g. storing keys in clear on the NAS and stealing the NAS | The encryption key is not stored on the NAS.  It is stored in clear on the client.  Loss of NAS does not mean loss of encryption key |




