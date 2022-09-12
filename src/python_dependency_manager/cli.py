from .core import PackageManagers, OperationCanceledException

def show_alternatives(prompt, alternative_list, default=None, show_cancel=True):
    """
    Show the list of alternatives
    :param alternative_list: a list of alternatives
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
    package_manager = default_package_manager

    choice = show_alternatives('Select a package manager', ['Pip', 'Conda'], 0 if default_package_manager == PackageManagers.pip else 1, True)
    if choice == 0:
        package_manager = PackageManagers.pip
    elif choice == 1:
        package_manager = PackageManagers.conda

    install_local = default_install_local

    if package_manager == PackageManagers.pip:
        install_local = show_yesno('Install locally', default_install_local)

    extra_command_line = show_open('Extra command line parameters', default_extra_command_line, True)
    return package_manager, install_local, extra_command_line


def select_package_alternative(package, alternatives_list):
    """
    Select a package alternative
    :param package: the package name
    :param alternatives_list: the list of alternatives
    :return:
    """
    if len(alternatives_list) == 1:
        return alternatives_list[0]

    choice = show_alternatives(f'Select a source for {package}', alternatives_list, default=0)
    return alternatives_list[choice]


