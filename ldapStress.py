#! /usr/bin/python
'''
Created on March 30, 2012

@author: Wolfgang Schupp
'''

import sys, os, ldap, getopt, threading, ldif
from time import time


def usage():
    print "Ldapstress: Ldap stress testing"
    print "Usage:", sys.argv[0], "-h hostname -p port -D username -w password -s searchfilter [-f inputfile] [-d]"
    print "-h  hostname"
    print "-p  port"
    print "-D  userdn"
    print "-w  password"
    print "-f  inputfiles, format: 1 string per line, multiple files allowed"
    print "-d  print search results"
    print "-v  be verbose"
    #print "-l  ldif output"
    print "-t  number of threads"
    print "searchfilter has to be in ldapsearch filter format" 
    print "   enclose in ' if necessary"
    print "   %s is allowed as replacement char when -f is used"
    print "   each occurance of %s will be replaced with one line of the input file"
    print "-r  raw input in inputfile: File contains complete ldap search filter"
    print 
    print "Example: ./ldapStress.py -f msisdns1.txt -f msisdns2.txt -s '(|(submsisdn=%s)(subxc1msisdn=%s))' -t 2"
    print


def main ():
    
    host = "" 
    port = 389
    user = "" 
    passwd = "" 
    global details
    details = False
    global verbose
    verbose = False
    rawinput = False
    fromfile = False
    searchinput = []
    sfilter = ""
    threadnum = 1
    thread = ""
    threads = []
    stats = []
    global lock
    lock = threading.RLock()
    
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h:p:D:w:f:ds:t:rv")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    # Parse Commandline options
    for o, a in opts:
        #if o in ("--help"):
        #    print "bla"
        #    usage()
        #    sys.exit(2)
        if o == "-h":
            host = a
        if o == "-p":
            port = int(a)
        if o == "-D":
            user = a
        if o == "-w":
            passwd = a
        if o == "-f":
            fromfile = True
            searchinput.append(getfromfile(a))
        if o == "-r":
            rawinput = True
        if o == "-d":
            details = True
        if o == "-s":
            sfilter = a
        if o == "-v":
            verbose = True
        if o == "-t":
            if (a >= "1"):
                threadnum = int(a)
            else:
                print "number of threads must be >= 1"
                sys.exit(2)

    
    if (len(sfilter) <= 1) and not rawinput:
        usage()
        sys.exit(2)
    
    for i in range(threadnum):
        if fromfile and (len(searchinput) >= i):
            sinput = searchinput[i - 1]
        elif fromfile:
            sinput = searchinput[0]
        else:
            sinput = ""
        
        thread = "t" + str(i)
            #print host, port, user, passwd, sinput, sfilter, rawinput
        thread = ThreadClass(host, port, user, passwd, sinput, sfilter, rawinput)
        thread.start()
        threads.append(thread)
           
    for t in threads:
        t.join()
        stats.append((t.getName(), t.runtime, t.counter, t.elapsed))
            
        
    for stat in stats:
        name, runtime, counter, elapsed = stat
        printstats(name, runtime, counter, elapsed)



def getfromfile(filename):
    msisdns = []
    
    fh = open(filename, 'r')
    for line in fh:
        msisdns.append(line.replace("\n", ""))
    return msisdns


    
def ldapsearch(tname, host, port, user, passwd, searchinput, sfilter, rawinput):
    
    counter = 1
    runtime = 0
    
    try:
        l = ldap.open(host, port)
        l.simple_bind_s(user, passwd)

        if (verbose):
            print "#", tname, "Successfully bound to server.\n"
        if (len(searchinput) > 0):  # We are using an inputfile with search data
            start = time()
            if (verbose):
                lock.acquire(blocking=1)
                print "#", tname, "Searchinput", searchinput
                lock.release()
                
            for i in searchinput:
                if (rawinput):      # Raw searchfilter in the file
                    searchfilter = i
                else:
                    searchfilter = sfilter.replace("%s", i)
                
                runtime += mysearch(l, searchfilter, tname)
                counter = counter + 1
                
                    #print tname, "Processed:", counter, "Entries"
            elapsed = time() - start
            #print tname, "Processed:", counter, "Entries ; Thread execution time:", "%.2f" % elapsed, "sec", "; Average Search time/entry:", "%d" % float((runtime / counter) * 1000), "ms"
            return (runtime, counter, elapsed)
             
        else: # We don't have an inputfile with searchfilters to process
            #print "single search"
            if (details) and (verbose):
                lock.acquire(blocking=1)
                print "#", tname, "Searchfilter:", sfilter
                lock.release()
            start = time()
            runtime = mysearch(l, sfilter, tname)
            elapsed = time() - start
            return (runtime, 1, elapsed)
                        
    except ldap.LDAPError, error_message:
        print "Couldn't Connect. %s " % error_message
        os._exit(3)
        


def mysearch(l, keyword, tname=""):
    
    basedn = "ou=subscribers,o=mobilkom.at"
    scope = ldap.SCOPE_SUBTREE
    ldapfilter = keyword
    attrib = None     # return all Attr

    try:
        start = time()
        result = l.search_s(basedn, scope, ldapfilter)
        elapsed = time() - start
        if (details):
            lock.acquire(blocking=1)
            for dn, entry in result:
                if (verbose):
                    print "#", tname, "Searchfilter:", ldapfilter
                handle_ldap_entry(dn, entry, tname)
                print "#", tname, "Num Results:", len(result), " ; Search took", "%d" % float(elapsed * 1000), "ms\n\n"
                
            lock.release()
                
        #print "Results:", len(result)
        return elapsed
        
    except ldap.LDAPError, error:
        print "Error", error
        

def handle_ldap_entry(dn, result, tname):
    
    print "#", tname, "Result:"
    ldifout = ldif.LDIFWriter(sys.stdout)
    ldifout.unparse(dn, result)
    
    
def printstats(tname, runtime, counter, elapsed):
    print "#",tname, "Processed:", counter, "Searches ; Thread execution time:", "%.2f" % elapsed, "sec", "; Average time/search:", "%d" % float((runtime / counter) * 1000), "ms", "; Searches/sec:", "%.2f" % float(1/(runtime / counter)), "#"
    
    
class ThreadClass(threading.Thread): 
    
    def __init__(self, host, port, user, passwd, searchinput, sfilter, rawinput):
        self.host, self.port, self.user, self.passwd, self.searchinput, self.sfilter, self.rawinput = host, port, user, passwd, searchinput, sfilter, rawinput
        threading.Thread.__init__(self)
    
    def run(self):
        self.runtime, self.counter, self.elapsed = ldapsearch(self.getName(),self.host, self.port, self.user, self.passwd, self.searchinput, self.sfilter, self.rawinput)
        

if __name__=='__main__':
    
    main()
    


