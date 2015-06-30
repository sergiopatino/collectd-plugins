

FILEPP := filepp -mp '$$' -dl

INFILES := $(wildcard in/*.py)

TARGETS := write_socket_json write_socket_keyval

all: $(TARGETS)

write_socket_json: $(INFILES) 
	$(FILEPP) -DNAME=$@ -DWRITER=socket -DFORMAT=json -o $@.py template.filepp

write_socket_keyval: $(INFILES) 
	$(FILEPP) -DNAME=$@ -DWRITER=socket -DFORMAT=keyval -o $@.py template.filepp

clean: 
	
