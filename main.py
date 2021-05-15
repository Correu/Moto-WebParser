'''
    main python file containing all the user interface aspects of the program
'''

import matplotlib.pyplot as pty
from fileReader import fileReader as fr

URL = 'https://racerxonline.com/category/injury-report'
fr.seleReader(URL)