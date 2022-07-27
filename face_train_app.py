from flask import Flask
import os
from face_train import Dataset, Model

app = Flask(__name__)  # 在当前文件下创建应用


@app.route("/")  # 装饰器，url，路由
def index():  # 试图函数
    user_num = len(os.listdir('./data/'))
    dataset = Dataset('./data/')
    dataset.load()
    model = Model()
    # 先前添加的测试build_model()函数的代码
    model.build_model(dataset, nb_classes=user_num)
    # 测试训练函数的代码
    model.train(dataset)
    model.save_model(file_path='./model/aggregate.face.model.h5')
    return "Face train completely,please go back to home"


if __name__ == "__main__":
    app.run(port='5005')