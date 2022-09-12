import tkinter as tk
from tkinter import ttk

from .config import PackageManagers
from .core import get_package_managers_list, OperationCanceledException


def center_window(window):
    window.update_idletasks()
    w, h = window.winfo_width(), window.winfo_height()
    window.wm_attributes('-alpha', 0)  # hide window
    window.update_idletasks()  # make sure the properties are updated
    window.geometry(f'{w}x{h}+0+0')  # 0,0 primary Screen
    window.update_idletasks()  # make sure the properties are updated
    s_width = window.winfo_screenwidth()
    s_height = window.winfo_screenheight()

    # if the screen is very wide, assume that they are two screens and try to center it in the left one
    # if you have a very large gaming display, you are out of luck
    if s_width > 2*s_height:
        s_width /= 2

    x = int((s_width / 2) - (w / 2))
    y = int((s_height / 2) - (h / 2))
    window.geometry(f'{w}x{h}+{x}+{y}')
    window.wm_attributes('-alpha', 1)  # show window


class InitDialog:
    def __init__(self, app, default_package_manager, default_install_local, default_extra_command_line):
        self.package_manager = default_package_manager
        self.local_install = default_install_local
        self.extra_command_line = default_extra_command_line
        self.app = app
        self.parent = ttk.Frame(app)
        self.parent.pack(fill="both", expand=True)
        self.ok = False
        self.app.title("Initialization options")
        self.body()
        self.buttonbox()

    def body(self):
        # print(type(frame)) # tkinter.Frame
        f = ttk.Frame(self.parent)
        pm_label = ttk.Label(f, text="Package Manager:")
        pm_label.pack(side="left", padx=(10,10))
        self.package_manager_box = ttk.Combobox(f, values=[p.capitalize() for p in get_package_managers_list()], state="readonly")
        self.package_manager_box.set(self.package_manager.name.capitalize())
        self.package_manager_box.pack(side="left", fill="x", expand=True)
        f.pack(fill="x", expand=True, padx=(10,10), pady=(10,0))

        f = ttk.Frame(self.parent)
        self.li_check = ttk.Checkbutton(f, text="Install locally")
        self.li_check.state(['!alternate'])
        self.li_check.state(['selected' if self.local_install else '!selected'])
        self.li_check.pack(side="left", padx=(10,10))
        f.pack(fill="x", padx=(10,10),pady=(10,10))

        f = ttk.Frame(self.parent)
        cl_label = ttk.Label(f, text="Extra command line options:")
        self.extra_command_line_entry = ttk.Entry(f)
        self.extra_command_line_entry.insert(0, self.extra_command_line)
        cl_label.pack(side="left", padx=(10,10))
        self.extra_command_line_entry.pack(side="left", fill="x", expand=True)
        f.pack(fill="x", expand=True, padx=(10,10))

    def ok_pressed(self):
        # print("ok")
        self.package_manager = PackageManagers[self.package_manager_box.get().lower()]
        self.local_install = self.li_check.instate(['selected'])
        self.extra_command_line = self.extra_command_line_entry.get()

        self.ok = True
        self.app.destroy()

    def cancel_pressed(self):
        self.ok = False
        self.app.destroy()


    def buttonbox(self):
        bboxFrame = ttk.Frame(self.parent)
        self.ok_button = ttk.Button(bboxFrame, text='OK', command=self.ok_pressed)
        self.ok_button.pack(side="left", padx=(20, 20))
        cancel_button = ttk.Button(bboxFrame, text='Cancel', command=self.cancel_pressed)
        cancel_button.pack(side="right", padx=(20, 20))
        bboxFrame.pack(pady=(10, 10))
        self.app.bind("<Return>", lambda event: self.ok_pressed())
        self.app.bind("<Escape>", lambda event: self.cancel_pressed())


def interactive_initialize(default_package_manager, default_install_local, default_extra_command_line):
    """
    Show the initialization interface
    :param default_package_manager: the default package manager
    :param default_install_local: the default install local flag
    :param default_extra_command_line: the default extra command line
    :return: the package manager, the install local flag, and the extra command line
    """
    root = tk.Tk()
    dialog = InitDialog(root, default_package_manager, default_install_local, default_extra_command_line)
    center_window(root)
    root.mainloop()
    if not dialog.ok:
        raise OperationCanceledException()
    return dialog.package_manager, dialog.local_install, dialog.extra_command_line


class SelectAlternativeDialog:
    def __init__(self, app, package_name, source_alternatives):
        self.package_name = package_name
        self.source_alternatives = source_alternatives
        self.app = app
        self.parent = ttk.Frame(app)
        self.parent.pack(fill="both", expand=True)
        self.alternative = None
        self.ok = False
        self.app.title(f'Choose an alternative for {package_name}')
        self.body()
        self.buttonbox()

    def body(self):
        title_label = ttk.Label(self.parent, text=f'Choose a source package for {self.package_name}')
        title_label.pack(pady=(10, 0))
        f = ttk.Frame(self.parent)
        alt_label = ttk.Label(f, text="Package:")
        alt_label.pack(side="left", padx=(10, 10))
        self.alternative_box = ttk.Combobox(f, values=self.source_alternatives, state="readonly")
        self.alternative_box.set(self.source_alternatives[0])
        self.alternative_box.pack(side="right", fill="x", expand=True)
        f.pack(fill="x", expand=True, padx=(10, 10), pady=(10, 0))

    def ok_pressed(self):
        # print("ok")
        self.alternative = self.alternative_box.get()
        self.ok = True
        self.app.destroy()

    def cancel_pressed(self):
        self.ok = False
        self.app.destroy()

    def buttonbox(self):
        bboxFrame = ttk.Frame(self.parent)
        self.ok_button = ttk.Button(bboxFrame, text='OK', command=self.ok_pressed)
        self.ok_button.pack(side="left", padx=(20, 20))
        cancel_button = ttk.Button(bboxFrame, text='Cancel', command=self.cancel_pressed)
        cancel_button.pack(side="right", padx=(20, 20))
        bboxFrame.pack(pady=(10, 10))
        self.app.bind("<Return>", lambda event: self.ok_pressed())
        self.app.bind("<Escape>", lambda event: self.cancel_pressed())


def select_package_alternative(package_name, source_alternatives):
    """
    Show the select alternative interface
    :param package_name: the package name
    :param source_alternatives: the source alternatives
    :return: the selected alternative
    """
    root = tk.Tk()
    dialog = SelectAlternativeDialog(root, package_name, source_alternatives)
    center_window(root)
    root.mainloop()
    if not dialog.ok:
        raise OperationCanceledException()
    return dialog.alternative