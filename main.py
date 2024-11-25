from Utils.AccountMananger import login_check
from Views.CMDViewer import login_menu


if __name__ == '__main__':
    if login_check():
        login_menu()