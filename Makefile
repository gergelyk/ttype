# CONFIGURE BELOW
NAME=ttype
VERSION=1.0.0
ARCH=amd64
MAN_SECTION=1

#files
F_SRC=$(NAME).py
F_BIN=$(NAME)
F_DEB=$(NAME)_$(VERSION)_$(ARCH).deb
F_SRC_TGZ=$(NAME)_$(VERSION)_src.tar.gz
F_HELP=$(NAME).help
F_MAN=$(NAME).$(MAN_SECTION).gz
F_DEB_CTL=$(NAME).ctl

#dirs
D_DEB=deb
D_EXP=export
D_UTL=utils
D_SRC=src
D_BIN=bin
D_MAN=man$(MAN_SECTION)

#paths
P_DEB=$(D_DEB)/$(F_DEB)
P_SRC_TGZ=$(D_EXP)/$(F_SRC_TGZ)
P_BIN=$(D_BIN)/$(F_BIN)
P_SRC=$(D_SRC)/$(F_SRC)
P_MAN=$(D_MAN)/$(F_MAN)
P_HELP=$(D_MAN)/$(F_HELP)
P_DEB=$(D_DEB)/$(F_DEB)
P_DEB_CTL=$(D_DEB)/$(F_DEB_CTL)

# USE THIS TARGET TO PRODUCE FILES FOR EXPORT
export: $(P_DEB)
	mkdir $(D_EXP)
	tar czvf $(P_SRC_TGZ) -C $(D_SRC) .
	cp $(P_DEB) $(D_EXP)
	$(D_UTL)/stamp.sh $(D_EXP)

# USE THIS TARGET TO INSTALL SOFTWARE ON LOCAL MACHINE
install: $(P_DEB)
	sudo dpkg -i $(P_DEB)

$(P_BIN):
	mkdir $(D_BIN)
	freeze -o $(D_BIN) $(P_SRC)
	make -C $(D_BIN)
	strip $(P_BIN)

$(P_MAN): $(P_BIN)
	help2man -v $(VERSION) -N echo -h '' -i $(P_HELP) | gzip -9 - > $(P_MAN)

$(P_DEB): $(P_BIN) $(P_MAN) $(D_DEB)/README.Debian $(P_DEB_CTL)
	cd deb; equivs-build $(F_DEB_CTL)
	lintian $(P_DEB)

clean:
	rm -fr $(D_BIN)
	rm man1/$(F_MAN)
	rm $(P_DEB)
	rm -fr $(D_EXP)


