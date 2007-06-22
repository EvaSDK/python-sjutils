import os, string, dircache, time, sys, md5, sha

def ismd5(DIR):
        hex="0123456789abcdef"
        if len(DIR) != 32:
                return False
        for a in DIR:
                if string.find(hex, a) == -1:
                        return False
        return True

def md5sum(f):
	f = file(f)
	md = md5.new()
	tmp = f.read(16384)
	while tmp:
		md.update(tmp)
		tmp = f.read(16384)
	f.close()
	return md.hexdigest()

def sha1sum(path):
    f = file(path)
    sh = sha.new()
    tmp = f.read(16384)
    while tmp:
        sh.update(tmp)
        tmp = f.read(16384)
    f.close()
    return sh.hexdigest()

def delete_recursive(path):
        if os.path.isfile(path):
                os.remove(path)
                return

        for FILE in dircache.listdir(path):
                file_or_dir = os.path.join(path, FILE)
                if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
                        delete_recursive(file_or_dir)
                else:
                        os.remove(file_or_dir)
        os.rmdir(path)

def delete_directory_branch(branch_path, path_limit=None):
    """ Try to delete branch_path until the directory is not empty
    and until it's not the limit path.
    Ex : delete_directory_branch('/root/toto/tata/titi', '/root') remove
    'titi' if empty and different to path_limit, then 'tata' if... etc
    """
    if os.path.isdir(branch_path):
        if path_limit and os.path.samefile(branch_path, path_limit):
            return
        try:
            os.rmdir(branch_path)
        except:
            pass
        else:
            delete_directory_branch( os.path.dirname(branch_path), path_limit )

def create_symlink(linkvalue, linkpath):
    if os.path.islink(linkpath): # linkpath exists and is a link
        if os.readlink(linkpath) != linkvalue: # comparing link value
            os.unlink(linkpath)
            os.symlink(linkvalue, linkpath)
    elif not os.path.exists(linkpath): # linkpath is not a link, maybe it doesn't exist
        os.symlink(linkvalue, linkpath)
    else: # linkpath is not a link, and exists, so it is a file
        os.unlink(linkpath)
        os.symlink(linkvalue, linkpath)

class Logger:
        "Sjutils log class"
        _file = ""
        _label = ""
        
        def __init__(self, logfile, label):
                self._file = open(logfile, "a", 1)
                self._label = label
                
        def write(self, str):
                t = time.gmtime()
                ts = "%02d/%02d/%02d GMT %02d:%02d:%02d " % (t[2], t[1], t[0], t[3], t[4], t[5])
                self._file.write(ts + "[" + self._label + "] " + str + "\n")

        def redirect_stdout_stderr(self):
                sys.stdout = sys.stderr = self._file

        def close(self):
                self._file.close()

