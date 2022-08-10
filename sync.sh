#!/bin/bash

#!/bin/sh
if ps -ef | grep -v grep | grep dicomSend.py ; then
        rsync -azvp --exclude 2020/ --exclude test.txt --exclude *.tgz /mnt/data/raid1/DicomShare/Roentgen /mnt/data/raid1/sendDCM/ ;
        rsync -azvp --exclude 2020/ --exclude test.txt --exclude *.tgz /mnt/data/raid1/DicomShare/MRT /mnt/data/raid1/sendDCM/ ;
        exit 0
else
        rsync -azvp --exclude 2020/ --exclude test.txt --exclude *.tgz /mnt/data/raid1/DicomShare/Roentgen /mnt/data/raid1/sendDCM/ ;
        rsync -azvp --exclude 2020/ --exclude test.txt --exclude *.tgz /mnt/data/raid1/DicomShare/MRT /mnt/data/raid1/sendDCM/ ;
        find /mnt/data/raid1/sendDCM/ -type f  -mmin -2880 -a -iname "*.dcm" > /root/python/files_to_copy ;
        python /root/python/dicomSend.py >> /root/python/log/dicomConvert.log ;
        exit 0
fi