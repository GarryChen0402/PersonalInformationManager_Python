import os

from Utils import load_all_users


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
    while True:
        print('-' * 45 + 'select_menu' + '-' * 44)
        print(f'Welcome to your personal information manager!\t{username}')
        print('Please select the followed operation: ')
        print('1. Display all users\' data')
        print('#\t:\tExit')
        print('-' * 100)
        choice = input('Please select your operation: ')
        if choice == '1':
            display_user_data(load_all_users())
        elif choice == '#':
            print(f'Thank you for using your personal information manager.\t{username}!')
            break
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    name = 'gyc'
    start_simulate_gui(name)