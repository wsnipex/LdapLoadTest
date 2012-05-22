LdapLoadTest
============

Python based LDAP load and performance testing tool


Dependency: python-ldap (http://pypi.python.org/pypi/python-ldap/)


Usage: ./ldapStress.py -h hostname -p port -D username -w password -s searchfilter [-f inputfile] [-d]
-h  hostname
-p  port
-D  userdn
-w  password
-f  inputfiles, format: 1 string per line, multiple files allowed
-d  print search results
-v  be verbose
-t  number of threads
searchfilter has to be in ldapsearch filter format
   enclose in ' if necessary
   %s is allowed as replacement char when -f is used
   each occurance of %s will be replaced with one line of the input file
-r  raw input in inputfile: File contains complete ldap search filter

Example: ./ldapStress.py -f file.txt -f file2.txt -s '(|(uid=%s)(cn=%s))' -t 2
