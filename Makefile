GPG_PASSPH=$(shell bash -c 'read -s gpg_passph; echo $$gpg_passph')
    
export: deb/ttype_1.0.0_amd64.deb
	mkdir export
	tar czvf export/ttype_1.0.0_src.tar.gz -C src .
	cp deb/ttype_1.0.0_amd64.deb export
	utils/sign.sh export

install: deb/ttype_1.0.0_amd64.deb
	sudo dpkg -i deb/ttype_1.0.0_amd64.deb

bin/ttype:
	mkdir bin
	freeze -o bin src/ttype.py
	make -C bin
	strip bin/ttype

man/ttype.1.gz: bin/ttype
	help2man -N bin/ttype -i man1/ttype.help | gzip -9 - > man1/ttype.1.gz

deb/ttype_1.0.0_amd64.deb: bin/ttype man/ttype.1.gz deb/README.Debian deb/ttype.ctl
	cd deb; equivs-build ttype.ctl
	lintian deb/*.deb

clean:
	rm -fr bin
	rm man1/ttype.1.gz
	rm deb/ttype_1.0.0_amd64.deb
	rm -fr export
