import os
import cv2
import sys
from createfold import CreateFolder
from face_train import Dataset, Model
from PIL import Image


def CatchPICFromVideo(window_name, camera_idx, catch_pic_num, path_name):
    # 检查输入路径是否存在——不存在就创建
    CreateFolder(path_name)

    cv2.namedWindow(window_name)

    # 视频来源，可以来自一段已存好的视频，也可以直接来自USB摄像头
    cap = cv2.VideoCapture(camera_idx)

    # 告诉OpenCV使用人脸识别分类器
    classfier = cv2.CascadeClassifier("D:\\opencv\\opencv\\build\\etc\\haarcascades\\haarcascade_frontalface_alt2.xml")

    # 识别出人脸后要画的边框的颜色，RGB格式
    color = (0, 255, 0)

    num = 0
    while cap.isOpened():
        ok, frame = cap.read()  # 读取一帧数据
        if not ok:
            break

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将当前桢图像转换成灰度图像
        print(grey)
        # 人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(grey, scaleFactor=1.2, minNeighbors=2, minSize=(32, 32))
        if len(faceRects) > 0:  # 大于0则检测到人脸
            for faceRect in faceRects:  # 单独框出每一张人脸
                x, y, w, h = faceRect

                if w > 200:

                    # 将当前帧保存为图片
                    img_name = '%s\%d.jpg' % (path_name, num)
                    # image = frame[y - 10: y + h + 10, x - 10: x + w + 10]
                    image = grey[y:y + h, x:x + w]  # 保存灰度人脸图,对原图像进行裁剪
                    cv2.imwrite(img_name, image)

                    num += 1
                    if num > (catch_pic_num):  # 如果超过指定最大保存数量退出循环
                        break

                    # 画出矩形框的时候稍微比识别的脸大一圈
                    # 参数(需要绘制的图片，起始点，终止点，颜色，厚度)
                    cv2.rectangle(frame, (x - 10, y - 10), (x + w + 10, y + h + 10), color, 2)

                    # 显示当前捕捉到了多少人脸图片了，这样站在那里被拍摄时心里有个数，不用两眼一抹黑傻等着
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, 'num:%d' % (num), (x + 30, y + 30), font, 1, (255, 0, 255), 4)

        # 超过指定最大保存数量结束程序
        if num > catch_pic_num:
            break

        # 显示图像
        cv2.imshow(window_name, frame)
        # 按键盘‘Esc’中断采集
        c = cv2.waitKey(10)
        if c & 0xFF == 27:
            break

    # 释放摄像头并销毁所有窗口
    # cap.release()
    # cv2.destroyAllWindows()
    # user_num = len(os.listdir('./data/'))
    #
    # dataset = Dataset('./data/')
    # dataset.load()
    #
    # model = Model()
    #
    # # 先前添加的测试build_model()函数的代码
    # model.build_model(dataset, nb_classes=user_num)
    # # 测试训练函数的代码
    # model.train(dataset)
    #
    # model.save_model(file_path='./model/aggregate.face.model.h5')


# 判断本程序是独立运行还是被调用
if __name__ == '__main__':
    if len(sys.argv) != 1:
        print("Usage:%s camera_id face_num_max path_name\r\n" % (sys.argv[0]))
    else:
        CatchPICFromVideo("截取人脸", 0, 200, './data/lhk')

