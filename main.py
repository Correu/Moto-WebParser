'''
    main python file containing all the user interface aspects of the program
'''

import matplotlib.pyplot as pty
from WebReader import webReader as wr

#make functionality to provide the hyperlink and the attribute to search for

URL = 'https://racerxonline.com/category/injury-report'
wr.mainPageReader(URL)