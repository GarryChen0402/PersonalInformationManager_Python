from DataClass.UserBase import Userbase


class CommonUser(Userbase):
    def __init__(self, uid, username, age, password='00000000', permission_level=2):
        super().__init__(uid, username, age, password, permission_level)

    def __str__(self):
        return  super().__str__()