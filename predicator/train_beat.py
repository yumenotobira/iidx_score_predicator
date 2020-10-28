# encoding: utf-8

import pathlib
import numpy as np
from keras.models import Sequential, model_from_json
from keras.layers import Dense, Masking
from keras.layers.recurrent import LSTM
from keras.optimizers import Adam
from keras import optimizers, regularizers
import os

# 取得するファイル名一覧
posixPath = list(pathlib.Path('chart_encoded').glob('*'))
fileNames = list(map(lambda x: x.name, posixPath))

# 譜面データと分布パラメーターの取得
charts = list()
params = list()

for fileName in fileNames:
    print(fileName)
    # 譜面データの取得
    f = open('chart_encoded/' + fileName)
    chart = f.readlines()
    f.close()

    chart = list(map(lambda x: x.replace('\n', ''), chart))

    l = list()
    for t in chart:
        l.append(list(map(lambda x: int(x), t.split(','))))

    charts.append(l)

    # パラメーターの取得
    f = open('gmm_result/' + fileName)
    param = f.read()
    f.close()

    param = param.replace('\n', ',')
    param = param.split(',')
    param.pop(-1)

    l = list()
    for t in param:
        l.append(float(t))

    params.append(l)

# 譜面データの長さを合わせる
# 最長の譜面に合わせ、短い分は-1で埋める
max_length = max(map(len, charts))
for i in range(len(charts)):
    padding = [[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]] * (max_length - len(charts[i]))
    charts[i].extend(padding)

# 学習用に形式を変換
charts = np.array(charts)
charts = charts.astype('float32')
params = np.array(params)
params = params.astype('float32')

# ネットワークの定義
model = Sequential()
model.add(Masking(input_shape=(None, 17), mask_value=-1.0))

weight_decay = 1e-4
model.add(LSTM(units=128, dropout=0.25, return_sequences=True))
model.add(LSTM(units=128, dropout=0.25, return_sequences=True))
model.add(LSTM(units=128, dropout=0.25, return_sequences=False,
    kernel_regularizer=regularizers.l2(weight_decay)))

model.add(Dense(units=15, activation='sigmoid'))

model.compile(loss='mse', optimizer=optimizers.Adam(), metrics=['accuracy'])

# 重みの読み込み
# 以前の重みを使って学習するときはコメントアウトを外す
#model.load_weights(os.path.join('./model/', 'model_weights.hdf5'))

history = model.fit(charts, params, batch_size=10, verbose=1, epochs=5, validation_split=0.1)

# 保存
json_string = model.to_json()
open(os.path.join('./model/', 'model.json'), 'w').write(json_string)
model.save_weights(os.path.join('./model/', 'model_weights.hdf5'))
