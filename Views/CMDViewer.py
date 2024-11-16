import os

from Utils import load_all_users, register_new_user, save_all_users


def display_user_data(users_data):
    print('-' * 45 + 'users_info' + '-' * 45)
    # print('users_info')
    print(f'Now, {len(users_data)} users are existed!')
    # f'{self.uid}\t{self.username}\t{self.password}\t{self.permission_level}\t{self.age}\t{self.emails}'
    print('uid\tusername\tpassword\tpermission_level\tself.age\temails')
    for user in users_data:
        print(user)

    print('-' * 45 + 'users_info_end' + '-' * 41)





def start_simulate_gui(username:str = 'Administrator'):
    users_list = load_all_users()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('-' * 45 + 'select_menu' + '-' * 44)
        print(f'Welcome to your personal information manager!\tAdministrator:{username}')
        print('Please select the followed operation: ')
        print('1\tDisplay all users\' data')
        print('2\tRegister new users\' data')
        print('#\t:\tExit')
        print('-' * 100)
        choice = input('Please select your operation: ')
        if choice == '1':
            display_user_data(users_list)
        elif choice == '2':
            users_list.append(register_new_user(len(users_list)))
        elif choice == '3':
            pass
        elif choice == '#':
            print(f'Thank you for using your personal information manager.\tAdministrator:{username}!')
            save_all_users(users_list)
            break
        input('Please press enter to continue!')

if __name__ == '__main__':
    name = 'gyc'
    start_simulate_gui(name)