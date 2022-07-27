import os
import sys

path_name = './data/linhongkun'


def CreateFolder(path):
    # 去除首位空格
    del_path_space = path.strip()
    # 去除尾部'\'
    del_path_tail = del_path_space.rstrip('\\')
    # 判读输入路径是否已存在
    isexists = os.path.exists(del_path_tail)
    if not isexists:
        os.makedirs(del_path_tail)
        return True
    else:
        return False


if __name__ == '__main__':
    if len(sys.argv) != 1:
        print("Usage:%s camera_id face_num_max path_name\r\n" % (sys.argv[0]))
    else:
        CreateFolder(path_name)
