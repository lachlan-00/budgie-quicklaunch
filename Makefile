INSTALLTEXT="quicklaunch is now installed"
INSTALLPATH="/usr/lib64/budgie-desktop/plugins"

install: install-req
	@echo $(INSTALLTEXT)

install-req:
	@mkdir -p $(INSTALLPATH)
	@cp main.ui $(INSTALLPATH) -f
	@cp pylaunch.py $(INSTALLPATH) -f
	@cp PyLaunch.plugin $(INSTALLPATH) -f
	sudo -u user budgie-panel --replace &

