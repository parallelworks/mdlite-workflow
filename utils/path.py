import os
import re
from parsl.data_provider.files import File

def Path (p):  # FIXME: separate iPath and oPath File objects?

    import re

    if p.startswith('/'):
        prefix = 'file://parslhost/'
    else:
        prefix = 'file://parslhost' + os.getcwd() + '/'

    #cwd = 'file://parslhost' + os.getcwd() + '/' # FIXME: determine how to specify this URL.  parslhost?  // or /// ?  abs vs rel?

    p = re.sub('//*','/',p)  # Remove doubled slashes
    p = re.sub('/\.$','/',p) # Change trailing /. to /

    hasdotslash = './' in p
    l = len(p)

    if hasdotslash:
        pass
    else:
        slashcount = p.count('/',1,l-2)
        if slashcount > 0:
            lastslash = p.rfind('/',1,l-2) # Dont count leading or trailing slashes
            if lastslash == -1:
                p = './' + p
            else:
                p = p[0:lastslash+1] + './' + p[lastslash+1:]
        else:
            p = './' + p  # FIXME: Verify that we should do this

    parts = p.rpartition('./')
    lp = parts[1]+parts[2] # Local path

    #f = File(cwd + p)
    f = File(prefix + p)

    f.local_path = lp

    local_start = f.path.rfind(lp)        # Find where local_path starts in full path (ie at end of full path)
    f.output_path = f.path[0:local_start] # output_path is full path with local_path removed from end

    # return p, lp # FIXME: Could set output_path here too.  Could later ssh mkdir -p of output_path

    #print(pathrep(f))
    return f
