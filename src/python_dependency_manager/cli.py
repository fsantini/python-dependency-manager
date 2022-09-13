from .config import DONT_INSTALL_TEXT
from .core import PackageManagers, get_package_managers_list
from .exceptions import OperationCanceledException


def show_alternatives(prompt, alternative_list, default=None, show_cancel=True):
    """
    Show the list of alternatives
    :param prompt: the prompt
    :param alternative_list: a list of alternatives
    :param default: the default choice
    :param show_cancel: whether to show the cancel option
    :return:
    """
    print(prompt)
    for i, alternative in enumerate(alternative_list):
        if default == i:
            is_default = '*'
        else:
            is_default = ' '
        print(f' {is_default} {i + 1}. {alternative}')

    cancel_option = str(i+2)

    if show_cancel:
        print(f'   {cancel_option}. Cancel')

    while True:
        if default is not None:
            choice = input(f'Enter your choice [default {default+1}]: ')
        else:
            choice = input('Enter your choice: ')

        if show_cancel and choice == cancel_option:
            raise OperationCanceledException()

        if default is not None and not choice:
            return default

        if choice in [str(i + 1) for i in range(len(alternative_list))]:
            return int(choice) - 1

        print('Invalid choice. Please try again')


def show_yesno(prompt, default=None, show_cancel=True):
    """
    Shows a prompt with a yes/no answer
    :param prompt: the prompt
    :param default: default value
    :param show_cancel: whether to give the cancel option
    :return:
    """

    if show_cancel:
        cancel_prompt = '/[C]ancel'
    else:
        cancel_prompt = ''

    if default is None:
        default_prompt = ''
    elif default:
        default_prompt = ' (Default: Yes)'
    else:
        default_prompt = ' (Default: No)'

    while True:
        choice = input(f'{prompt} ([Y]es/[N]o{cancel_prompt}){default_prompt}? ')

        if not choice and default is not None:
            return default

        choice_char = choice[0].lower()
        if show_cancel and choice_char == 'c':
            raise OperationCanceledException()

        if choice_char == 'y':
            return True
        elif choice_char == 'n':
            return False

        print('Invalid choice. Please try again')


def show_open(prompt, default=None, show_cancel=True):
    print(prompt)
    if default is not None:
        print(f' [Default: {default}]')
        if show_cancel:
            cancel_prompt = '/[c]ancel'
        else:
            cancel_prompt = ''
        while True:
            choice = input(f'Accept default ([Y]es/[n]o{cancel_prompt}]? ')
            if not choice:
                return default
            choice_char = choice[0].lower()
            if show_cancel and choice_char == 'c':
                raise OperationCanceledException()
            if choice_char == 'y':
                return default
            elif choice_char == 'n':
                break
            print('Invalid choice. Please try again')

    if show_cancel:
        cancel_prompt = ' [type "cancel" to cancel]'
    else:
        cancel_prompt = ''

    choice = input(f'Your input{cancel_prompt}>')
    if choice.strip().lower() == 'cancel' or choice.strip().lower() == '"cancel"':
        raise OperationCanceledException()

    return choice


def interactive_initialize(default_package_manager, default_install_local, default_extra_command_line):
    """
    Show the initialization interface
    :return:
    """

    # The package manager enum always contains "common" at 1, which is not offered as an option, so the returned
    # choice, which starts at zero, always corresponds to the package manager index-2
    choice = show_alternatives('Select a package manager', [x.capitalize() for x in get_package_managers_list()],
                               default_package_manager.value - 2, True)
    package_manager = PackageManagers(choice + 2)

    install_local = default_install_local

    if package_manager == PackageManagers.pip:
        install_local = show_yesno('Install locally', default_install_local)

    extra_command_line = show_open('Extra command line parameters', default_extra_command_line, True)
    return package_manager, install_local, extra_command_line


def select_package_alternative(package, alternatives_list, optional=False):
    """
    Select a package alternative
    :param package: the package name
    :param alternatives_list: the list of alternatives
    :param optional: whether the package is optional
    :return:
    """
    if len(alternatives_list) == 1 and not optional:
        return alternatives_list[0]

    if optional:
        display_alternatives = [DONT_INSTALL_TEXT] + alternatives_list
    else:
        display_alternatives = alternatives_list

    opt_req = 'Optional' if optional else 'Required'

    choice = show_alternatives(f'Select a source for {package} ({opt_req})', display_alternatives, default=0)
    if optional:
        if choice == 0:
            return None
        else:
            return alternatives_list[choice - 1]
    return alternatives_list[choice]
