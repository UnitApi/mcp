genexecutable:
	cp main.py unitmcp
	sed  -i '1i #!/usr/bin/python\n' unitmcp

install: genexecutable
	sudo cp unitmcp /usr/bin/
	sudo chmod +x /usr/bin/unitmcp
	rm unitmcp