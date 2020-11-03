# encoding: utf-8

import pathlib
import numpy as np
from keras.models import model_from_json, Model
from keras.layers import Dense, Masking, Input, Activation, concatenate, Dropout
from keras.layers.recurrent import LSTM
from keras.optimizers import Adam
from keras import optimizers, regularizers, callbacks
from keras import backend as K
import os
import pickle

def norm_kl_divergence(mean_true, mean_pred, sd_true, sd_pred):
    return K.log(sd_pred / sd_true) + (K.square(sd_true) + K.square(mean_true - mean_pred)) / (2.0 * K.square(sd_pred)) - 1.0 / 2.0

def custom_loss(y_true, y_pred):
    weight_true = y_true[:, 0:5]
    weight_pred = y_pred[:, 0:5]
    mean_true = y_true[:, 5:10]
    mean_pred = y_pred[:, 5:10]
    sd_true = y_true[:, 10:15]
    sd_pred = y_pred[:, 10:15]

    sum_a = 0
    for i in range(5):
        weight_a = weight_true[:, i]
        mean_a = mean_true[:, i]
        sd_a = sd_true[:, i]

        sum_b = 0
        sum_c = 0
        for j in range(5):
            weight_b = weight_true[:, j]
            mean_b = mean_true[:, j]
            sd_b = sd_true[:, j]
            weight_c = weight_pred[:, j]
            mean_c = mean_pred[:, j]
            sd_c = sd_pred[:, j]

            kl_ab = norm_kl_divergence(mean_a, mean_b, sd_a, sd_b)
            kl_ac = norm_kl_divergence(mean_a, mean_c, sd_a, sd_c)

            if j == 0:
              sum_b = weight_b * K.exp(-kl_ab)
              sum_c = weight_c * K.exp(-kl_ac)
            else:
              sum_b = sum_b + weight_b * K.exp(-kl_ab)
              sum_c = sum_c + weight_c * K.exp(-kl_ac)

        if i == 0:
          sum_a = weight_a * K.log(sum_b/sum_c)
        else:
          sum_a = sum_a + weight_a * K.log(sum_b/sum_c)

    loss = sum_a
    return loss

# 取得するファイル名一覧
posixPath = list(pathlib.Path('/content/drive/My Drive/beatmania/chart_encoded').glob('*'))
fileNames = list(map(lambda x: x.name, posixPath))

# 譜面データと分布パラメーターの取得
charts = list()
params = list()

index = 1
for fileName in fileNames:
    print(str(index) + ": " + fileName)
    index += 1
    for number in range(1):
      # 譜面データの取得
      chart = np.loadtxt('/content/drive/My Drive/beatmania/chart_encoded/'+ fileName, delimiter=',')

      # BPMを1/100倍する
      chart[:, -1] /= 100

      # 96で分割できるように譜面の長さを調整する
      for i in range(96 - (len(chart) - int(len(chart) / 96) * 96)):
        chart = np.append(chart, np.full((1, 9), -1), axis=0)

      splitted = np.split(chart, len(chart)/96)
      splitted_chart = np.empty((0, 96*9))
      for s in splitted:
        flatten = np.reshape(s, [96*9])
        splitted_chart = np.append(splitted_chart, [flatten], axis=0)

      charts.append(splitted_chart)

      # パラメーターの取得
      f = open('/content/drive/My Drive/beatmania/gmm_result/' + fileName)
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
    padding = [[-1]*(9*96)] * (max_length - len(charts[i]))
    if len(padding) != 0:
      charts[i] = np.append(charts[i], padding, axis=0)

# 学習用に形式を変換
charts = np.array(charts)
charts = charts.astype('float32')
params = np.array(params)
params = params.astype('float32')

# ネットワークの定義
model_input = Input(shape=(None, 9*96))
mask = Masking(mask_value=-1.0)(model_input)

weight_decay = 1e-4
mid1 = LSTM(units=128, dropout=0.25, return_sequences=True)(mask)
mid1 = LSTM(units=128, dropout=0.25, return_sequences=True)(mid1)
mid2 = LSTM(units=128, dropout=0.25, return_sequences=True)(mid1)
mid2 = LSTM(units=128, dropout=0.25, return_sequences=True)(mid2)
mid2 = LSTM(units=128, dropout=0.25, return_sequences=True)(mid2)
mid3 = LSTM(units=128, dropout=0.25, return_sequences=False,
        kernel_regularizer=regularizers.l2(weight_decay))(mid2)

additional_dense1 = Dense(5)(mid3)
output1 = Activation('softmax')(additional_dense1)
additional_dense2 = Dense(10)(mid3)
output2 = Activation('sigmoid')(additional_dense2)
merged = concatenate([output1, output2])
model = Model(inputs=[model_input], outputs=[merged])

model.compile(loss=custom_loss, optimizer=optimizers.Adam(), metrics=['accuracy'])

# 重みの読み込み
# 以前の重みを使って学習するときはコメントアウトを外す
#model.load_weights(os.path.join('/content/drive/My Drive/beatmania/model/', 'model_weights.hdf5'))

fpath = os.path.join('/content/drive/My Drive/beatmania/model/', 'model_weights.{epoch:04d}-{val_loss:.2f}.hdf5')
cp_cb = callbacks.ModelCheckpoint(filepath=fpath, monitor='val_loss', verbose=1, save_weights_only = True, save_best_only=True, mode='auto')

history = model.fit(charts, params, batch_size=32, verbose=0, initial_epoch=0, epochs=5000, validation_split=0.1, callbacks=[cp_cb])

# 保存
json_string = model.to_json()
open(os.path.join('/content/drive/My Drive/beatmania/model/', 'model.json'), 'w').write(json_string)
model.save_weights(os.path.join('/content/drive/My Drive/beatmania/model/', 'model_weights.hdf5'))
with open(os.path.join('/content/drive/My Drive/beatmania/model/', 'history.pickle'), 'wb') as file_pi:
        pickle.dump(history.history, file_pi)
