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

# 取得するファイル名一覧
posixPath = list(pathlib.Path('/content/drive/My Drive/beatmania/chart_encoded_rename').glob('*'))
fileNames = list(map(lambda x: x.name, posixPath))

# 譜面データと分布パラメーターの取得
charts = list()
params = list()

index = 1
for fileName in fileNames:
    print(str(index) + ": " + fileName)
    index += 1
    for number in range(1):
      fileNameWithNumber = fileName + "_" + "{:02d}".format(number)
      # 譜面データの取得
      chart = np.loadtxt('/content/drive/My Drive/beatmania/rotate_chart_encoded/'+ fileNameWithNumber, delimiter=',')

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
      f = open('/content/drive/My Drive/beatmania/gmm_result_rename/' + fileName)
      param = f.read()
      f.close()

      param = param.replace('\n', ',')
      param = param.split(',')
      param.pop(-1)
      # sdを100倍してオーダーを上げる
      param = list(map(lambda x: float(x), param))
      param[10:15] = list(map(lambda x: x*100, param[10:15]))

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

mid1w = LSTM(units=128, dropout=0.25, return_sequences=True)(mask)
mid2w = LSTM(units=128, dropout=0.25, return_sequences=True)(mid1w)
mid3w = LSTM(units=128, dropout=0.25, return_sequences=False,
        kernel_regularizer=regularizers.l2(weight_decay))(mid2w)
mid1m = LSTM(units=128, dropout=0.25, return_sequences=True)(mask)
mid2m = LSTM(units=128, dropout=0.25, return_sequences=True)(mid1m)
mid3m = LSTM(units=128, dropout=0.25, return_sequences=False,
        kernel_regularizer=regularizers.l2(weight_decay))(mid2m)
mid1s = LSTM(units=128, dropout=0.25, return_sequences=True)(mask)
mid2s = LSTM(units=128, dropout=0.25, return_sequences=True)(mid1s)
mid3s = LSTM(units=128, dropout=0.25, return_sequences=False,
        kernel_regularizer=regularizers.l2(weight_decay))(mid2s)

for_w = Dense(128, activation='relu')(mid3w)
for_w = Dropout(0.25)(for_w)
for_m = Dense(128, activation='relu')(mid3m)
for_m = Dropout(0.25)(for_m)
for_s = Dense(128, activation='relu')(mid3s)
for_s = Dropout(0.25)(for_s)

additional_dense1 = Dense(5)(for_w)
output1 = Activation('softmax')(additional_dense1)
additional_dense2 = Dense(5)(for_m)
output2 = Activation('sigmoid')(additional_dense2)
additional_dense3 = Dense(5)(for_s)
output3 = Activation('relu')(additional_dense3)

merged = concatenate([output1, output2, output3])
model = Model(inputs=[model_input], outputs=[merged])
model.compile(loss='mean_absolute_error', optimizer=optimizers.Adam(), metrics=['accuracy'])

fpath = os.path.join('/content/drive/My Drive/beatmania/model/', 'model_weights.{epoch:05d}-{val_loss:.2f}.hdf5')
cp_cb = callbacks.ModelCheckpoint(filepath=fpath, monitor='val_loss', verbose=0, save_weights_only = True, save_best_only=True, mode='auto')
cp_es = callbacks.EarlyStopping(monitor='val_loss', patience=100, verbose=1, mode='auto')

history = model.fit(charts, params, batch_size=32, verbose=2, initial_epoch=0, epochs=1000, validation_split=0.1, callbacks=[cp_cb, cp_es])

# 保存
json_string = model.to_json()
open(os.path.join('/content/drive/My Drive/beatmania/model/', 'model.json'), 'w').write(json_string)
model.save_weights(os.path.join('/content/drive/My Drive/beatmania/model/', 'model_weights.hdf5'))
with open(os.path.join('/content/drive/My Drive/beatmania/model/', 'history.pickle'), 'wb') as file_pi:
        pickle.dump(history.history, file_pi)
