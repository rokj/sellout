import os

# set stuff
extensions = [ # files that we are interested in (without dots at the beginning)
    'html',
    'js',
    'css',
    'py',
]

ignore = [ # ignore files which names start with any of these:
    './static/jquery',
    './static/big',
    './static/keyboard/',
    './static/fuckyeah/',
    './admin',
    './tmp/',
]

############ no fiddling with code below ############
extensions = ["." + x for x in extensions]
size = 0

ignore_this = False
this_size = 0

for root, dir, files in os.walk("."):
    for f in files:
        path = os.path.join(root, f)
        if os.path.splitext(f)[1].lower() in extensions: # interested in this file?
            # or should it be ignored?
            for i in ignore:
                if path.startswith(i):
                    ignore_this = True
                    break

            if not ignore_this:
                this_size = os.path.getsize(path)
                print "{: >9d}: {}".format(this_size, path)
                
                size += this_size
            
            ignore_this = False
                
print "Project size: {: 7.3f} kB".format(float(size)/1024.)
