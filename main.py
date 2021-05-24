'''
    main python file containing all the user interface aspects of the program
'''

import matplotlib.pyplot as pty
from WebReader import webReader as wr

URL = 'https://racerxonline.com/category/injury-report'
wr.mainPageReader(URL)