#!/bin/bash
echo 'GPG PASSPHRASE:'
read -s PASSPHRASE
echo $PASSPHRASE

cd $1

for file in `find . -iname '??*'`; do 
    gpg --passphrase $PASSPHRASE --detach-sign $file
    md5sum $file > $file.md5
done


