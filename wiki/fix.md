# Fixes
## 1. The HD does not want to be mounted

Try to mount it on an Ubuntu machine: 

```sh
sudo mount -t ntfs /dev/sdc1 /media/akoel/
```

result:
```sh
Error mounting /dev/sdc1 at /media/: Command-line `mount -t "ntfs" -o "uhelper=udisks2,nodev,nosuid,uid=1000,gid=1000" "/dev/sdc1" "/media/sorin/LICENTA"' exited with non-zero exit status 13: $MFTMirr does not match $MFT (record 0).
Failed to mount '/dev/sdc1': Input/output error
NTFS is either inconsistent, or there is a hardware fault, or it's a
SoftRAID/FakeRAID hardware. In the first case run chkdsk /f on Windows
then reboot into Windows twice. The usage of the /f parameter is very
important! If the device is a SoftRAID/FakeRAID then first activate
it and mount a different device under the /dev/mapper/ directory, (e.g.
/dev/mapper/nvidia_eahaabcc1). Please see the 'dmraid' documentation
for more details.
```

Fix:
```sh
sudo apt-get install ntfs-3g
sudo ntfsfix /dev/sdc1
```

Output:
```sh
Mounting volume... 
FAILED Attempting to correct errors... 
Processing $MFT and $MFTMirr... Reading $MFT... OK Reading $MFTMirr... OK 
Comparing $MFTMirr to $MFT... 
FAILED Correcting differences in $MFTMirr record 0...OK 
Processing of $MFT and $MFTMirr completed successfully. 
Setting required flags on partition... OK 
Going to empty the journal ($LogFile)... OK 
NTFS volume version is 3.1. NTFS partition /dev/sdb3 was processed successfully.
```


After this step you should be able to access your external drive partition as usual
