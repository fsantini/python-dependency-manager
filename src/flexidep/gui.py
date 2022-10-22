"""GUI implementation."""

import tkinter as tk
from contextlib import contextmanager
from tkinter import messagebox, ttk

from .config import DONT_INSTALL_TEXT, PackageManagers
from .core import get_package_managers_list
from .exceptions import OperationCanceledError


def center_window(window):
    """Center a window on the screen."""
    window.update_idletasks()
    width, height = window.winfo_width(), window.winfo_height()
    window.wm_attributes('-alpha', 0)  # hide window
    window.update_idletasks()  # make sure the properties are updated
    window.geometry(f'{width}x{height}+0+0')  # 0,0 primary Screen
    window.update_idletasks()  # make sure the properties are updated
    s_width = window.winfo_screenwidth()
    s_height = window.winfo_screenheight()

    # if the screen is very wide, assume that they are two screens and try to center it in the left one
    # if you have a very large gaming display, you are out of luck
    if s_width > 2 * s_height:
        s_width /= 2

    x_pos = int((s_width / 2) - (width / 2))
    y_pos = int((s_height / 2) - (height / 2))
    window.geometry(f'{width}x{height}+{x_pos}+{y_pos}')
    window.wm_attributes('-alpha', 1)  # show window


class InitDialog:
    """GUI dialog class for YES/NO choices."""

    def __init__(
        self,
        app,
        default_package_manager,
        default_install_local,
        default_extra_command_line,
    ):
        """Initialize an InitDialog instance."""
        self.package_manager = default_package_manager
        self.local_install = default_install_local
        self.extra_command_line = default_extra_command_line
        self.app = app
        self.parent = ttk.Frame(app)
        self.parent.pack(fill='both', expand=True)
        self.ok = False
        self.app.title('Initialization options')
        self.body()
        self.buttonbox()

    def body(self):
        """Populate the body of the dialog."""
        frame = ttk.Frame(self.parent)
        pm_label = ttk.Label(frame, text='Package Manager:')
        pm_label.pack(side='left', padx=(10, 10))
        self.package_manager_box = ttk.Combobox(
            frame,
            values=[p.capitalize() for p in get_package_managers_list()],
            state='readonly',
        )
        self.package_manager_box.set(self.package_manager.name.capitalize())
        self.package_manager_box.pack(side='left', fill='x', expand=True)
        frame.pack(fill='x', expand=True, padx=(10, 10), pady=(10, 0))

        frame = ttk.Frame(self.parent)
        self.li_check = ttk.Checkbutton(frame, text='Install locally')
        self.li_check.state(['!alternate'])
        self.li_check.state(['selected' if self.local_install else '!selected'])
        self.li_check.pack(side='left', padx=(10, 10))
        frame.pack(fill='x', padx=(10, 10), pady=(10, 10))

        frame = ttk.Frame(self.parent)
        cl_label = ttk.Label(frame, text='Extra command line options:')
        self.extra_command_line_entry = ttk.Entry(frame)
        self.extra_command_line_entry.insert(0, self.extra_command_line)
        cl_label.pack(side='left', padx=(10, 10))
        self.extra_command_line_entry.pack(side='left', fill='x', expand=True)
        frame.pack(fill='x', expand=True, padx=(10, 10))

    def ok_pressed(self):
        """Callback-function called for the <OK> button."""
        self.package_manager = PackageManagers[self.package_manager_box.get().lower()]
        self.local_install = self.li_check.instate(['selected'])
        self.extra_command_line = self.extra_command_line_entry.get()

        self.ok = True
        self.app.destroy()

    def cancel_pressed(self):
        """Callback-function called for the <Cancel> button."""
        self.ok = False
        self.app.destroy()

    def buttonbox(self):
        """Create a button box with <OK> and <Cancel> buttons."""
        bbox_frame = ttk.Frame(self.parent)
        self.ok_button = ttk.Button(bbox_frame, text='OK', command=self.ok_pressed)
        self.ok_button.pack(side='left', padx=(20, 20))
        cancel_button = ttk.Button(bbox_frame, text='Cancel', command=self.cancel_pressed)
        cancel_button.pack(side='right', padx=(20, 20))
        bbox_frame.pack(pady=(10, 10))
        self.app.bind('<Return>', lambda event: self.ok_pressed())
        self.app.bind('<Escape>', lambda event: self.cancel_pressed())


def interactive_initialize(default_package_manager, default_install_local, default_extra_command_line):
    """
    Show the initialization interface.

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
        raise OperationCanceledError()
    return dialog.package_manager, dialog.local_install, dialog.extra_command_line


class SelectAlternativeDialog:
    """GUI dialog class for a list of alternative choices."""

    def __init__(self, app, package_name, source_alternatives, optional=False):
        """Initialize a SelectAlternativeDialog instance."""
        self.package_name = package_name
        self.source_alternatives = source_alternatives
        self.app = app
        self.optional = optional
        self.parent = ttk.Frame(app)
        self.parent.pack(fill='both', expand=True)
        self.alternative = None
        self.ok = False
        self.app.title(f'Choose a source for {package_name}')
        self.body()
        self.buttonbox()

    def body(self):
        """Populate the body of the dialog."""
        opt_req = 'Optional' if self.optional else 'Required'
        title_label = ttk.Label(
            self.parent,
            text=f'Choose a source package for {self.package_name} ({opt_req})',
        )
        title_label.pack(padx=(10, 10), pady=(10, 0))
        frame = ttk.Frame(self.parent)
        alt_label = ttk.Label(frame, text='Package:')
        alt_label.pack(side='left', padx=(10, 10))
        self.alternative_box = ttk.Combobox(frame, values=self.source_alternatives, state='readonly')
        self.alternative_box.set(self.source_alternatives[0])
        self.alternative_box.pack(side='right', fill='x', expand=True)
        frame.pack(fill='x', expand=True, padx=(10, 10), pady=(10, 0))

    def ok_pressed(self):
        """Callback-function called for the <OK> button."""
        self.alternative = self.alternative_box.get()
        self.ok = True
        self.app.destroy()

    def cancel_pressed(self):
        """Callback-function called for the <Cancel> button."""
        self.ok = False
        self.app.destroy()

    def buttonbox(self):
        """Create a button box with <OK> and <Cancel> buttons."""
        bbox_frame = ttk.Frame(self.parent)
        self.ok_button = ttk.Button(bbox_frame, text='OK', command=self.ok_pressed)
        self.ok_button.pack(side='left', padx=(20, 20))
        cancel_button = ttk.Button(bbox_frame, text='Cancel', command=self.cancel_pressed)
        cancel_button.pack(side='right', padx=(20, 20))
        bbox_frame.pack(pady=(10, 10))
        self.app.bind('<Return>', lambda event: self.ok_pressed())
        self.app.bind('<Escape>', lambda event: self.cancel_pressed())


def select_package_alternative(package_name, source_alternatives, optional=False):
    """
    Show the select alternative interface.

    :param package_name: the package name
    :param source_alternatives: the source alternatives
    :param optional: if the selection is optional
    :return: the selected alternative
    """
    if len(source_alternatives) == 1 and not optional:
        return source_alternatives[0]

    if optional:
        display_alternatives = [DONT_INSTALL_TEXT] + source_alternatives
    else:
        display_alternatives = source_alternatives

    root = tk.Tk()
    dialog = SelectAlternativeDialog(root, package_name, display_alternatives, optional)
    center_window(root)
    root.mainloop()
    if not dialog.ok:
        raise OperationCanceledError()
    if optional and dialog.alternative == DONT_INSTALL_TEXT:
        return None

    return dialog.alternative


@contextmanager
def tk_context_manager():
    """Context manager for Tkinter."""
    root = tk.Tk()
    try:
        yield root
    finally:
        root.destroy()


def notify_uninstall(package):
    """
    Notify the user that a package will be uninstalled.

    :param package: the package name
    :return: True if the user accepts, False otherwise
    """
    with tk_context_manager() as root:
        root.withdraw()
        return messagebox.askyesno(
            'Uninstall package', f'Uninstall {package} (Note: answering no will abort the execution)?'
        )
