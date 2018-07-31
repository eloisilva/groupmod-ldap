clean:
	@echo "Cleaning control files"
	@if test -d groupadd.egg-info ;then rm -r groupadd.egg-info/ ;fi
	@if test -d build ;then rm -r build/ ;fi
	@if test -d dist ;then rm -r dist/ ;fi

clean-py:
	@echo "Cleaning python artifacts"
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete

clean-all: clean-py clean

test:
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -a -u a0046772 grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -n grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -a -u a0046772,a0047819 grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -d -u a0046772 grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -r grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -d -u a0046772 grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -d -u a0046772,a0047819 grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -r grp1
	@/usr/bin/python3 groupmod-ldap.py -D a0046772 -w xxx -a -u a0046772 grp1

all: clean-all test
