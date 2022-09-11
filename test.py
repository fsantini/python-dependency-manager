import sys
import os

from tkinter import *

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from python_dependency_manager import DependencyManager

if __name__ == '__main__':
    dm = DependencyManager()
    dm.load_file('test.cfg')
    print(dm.pkg_to_install)

    a = 1
    def set_a():
        global a
        a = 2
        root.destroy()

    root = Tk()
    Button(root, text="Quit", command=set_a).pack()  # button to close the window
    root.mainloop()
    print("First loop ended", a)
    root = Tk()
    Button(root, text="Quit2", command=root.destroy).pack()  # button to close the window
    root.mainloop()
    print("Second loop ended")