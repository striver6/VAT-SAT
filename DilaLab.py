
from keras.models import *
from keras.layers import Input, merge, Conv2D, MaxPooling2D, UpSampling2D, Dropout,concatenate,BatchNormalization,AveragePooling2D,LeakyReLU,MaxPool2D,add
from keras.optimizers import *
from keras.callbacks import ModelCheckpoint,ReduceLROnPlateau
from data import *
import keras.backend.tensorflow_backend as KTF


from numba import jit

import warnings
warnings.filterwarnings('ignore')

import os


def dice_coef(y_true, y_pred, smooth=1, weight=1):
    """
    加权后的dice coefficient
    """
    y_true = y_true[:, :, :, -1]
    y_pred = y_pred[:, :, :, -1]
    intersection = K.sum(y_true * y_pred)
    union = K.sum(y_true) + weight * K.sum(y_pred)
    return (2. * intersection + smooth) / (union + smooth)


def dice_coef_loss(y_true, y_pred):
    """
    目标函数
    """
    return 1 - dice_coef(y_true, y_pred)

def f1_score(y_true, y_pred, smooth=1):
    """
    f1 score，用于训练过程中选择模型
    """
    y_true = y_true[:,:,:,-1]
    y_pred = y_pred[:,:,:,-1]
    c1 = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    c2 = K.sum(K.round(K.clip(y_pred, 0, 1)))
    c3 = K.sum(K.round(K.clip(y_true, 0, 1)))
    f1_score = (2*c1+smooth)/(c2+c3+smooth)
    return f1_score

class myDilaLab(object):

    def __init__(self, img_rows = 512, img_cols = 512):

        self.img_rows = img_rows
        self.img_cols = img_cols

    def load_data(self):

        mydata = dataProcess(self.img_rows, self.img_cols)
        imgs_train, imgs_mask_train = mydata.load_train_data()
        imgs_test = mydata.load_test_data()
        return imgs_train, imgs_mask_train, imgs_test



    def get_DilaLab(self):
        inputs = Input((self.img_rows, self.img_cols, 1))

        conv1 = Conv2D(16, 3, activation='relu', padding='same', kernel_initializer='he_normal')(inputs)
        conv1 = BatchNormalization()(conv1)
        conv1 = Conv2D(16, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv1)
        conv1 = BatchNormalization()(conv1)
        pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

        conv2 = Conv2D(32, 3, activation='relu', padding='same', kernel_initializer='he_normal')(pool1)
        conv2 = BatchNormalization()(conv2)
        conv2 = Conv2D(32, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv2)
        conv2 = BatchNormalization()(conv2)
        pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

        conv3 = Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(pool2)
        conv3 = BatchNormalization()(conv3)
        conv3 = Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv3)
        conv3 = BatchNormalization()(conv3)
        pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

        conv4 = Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(pool3)
        conv4 = BatchNormalization()(conv4)
        conv4 = Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv4)
        conv4 = BatchNormalization()(conv4)
        pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

        conv5 = Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(pool4)
        conv5 = BatchNormalization()(conv5)
        conv5 = Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv5)
        conv5 = BatchNormalization()(conv5)
        pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)

        conv6 = Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(pool5)
        conv6 = BatchNormalization()(conv6)
        conv6 = Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv6)
        conv6 = BatchNormalization()(conv6)
        pool6 = MaxPooling2D(pool_size=(2, 2))(conv6)

        conv71 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(1, 1), kernel_initializer='he_normal')(pool6)
        conv72 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(2, 2), kernel_initializer='he_normal')(pool6)
        conv73 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(4, 4), kernel_initializer='he_normal')(pool6)
        conv74 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(8, 8), kernel_initializer='he_normal')(pool6)
        conv75 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(16, 16), kernel_initializer='he_normal')(pool6)
        conv76 = Conv2D(1024, 3, activation='relu', padding='same', dilation_rate=(32, 32), kernel_initializer='he_normal')(pool6)
        conv7 = add([conv71,conv72,conv73,conv74,conv75,conv76])

        up8 = Conv2D(512, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv7))
        merge8 = concatenate([conv6, up8], axis=3)
        conv8 = Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge8)
        conv8 = BatchNormalization()(conv8)
        conv8 = Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv8)
        conv8 = BatchNormalization()(conv8)

        up9 = Conv2D(256, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv8))
        merge9 = concatenate([conv5, up9], axis=3)
        conv9 = Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge9)
        conv9 = BatchNormalization()(conv9)
        conv9 = Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv9)
        conv9 = BatchNormalization()(conv9)

        up10 = Conv2D(128, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv9))
        merge10 = concatenate([conv4, up10], axis=3)
        conv10 = Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge10)
        conv10 = BatchNormalization()(conv10)
        conv10 = Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv10)
        conv10 = BatchNormalization()(conv10)

        up11 = Conv2D(64, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv10))
        merge11 = concatenate([conv3, up11], axis=3)
        conv11 = Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge11)
        conv11 = BatchNormalization()(conv11)
        conv11 = Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv11)
        conv11 = BatchNormalization()(conv11)

        up12 = Conv2D(32, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv11))
        merge12 = concatenate([conv2, up12], axis=3)
        conv12 = Conv2D(32, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge12)
        conv12 = BatchNormalization()(conv12)
        conv12 = Conv2D(32, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv12)
        conv12 = BatchNormalization()(conv12)

        up13 = Conv2D(16, 2, activation='relu', padding='same', kernel_initializer='he_normal')(
            UpSampling2D(size=(2, 2))(conv12))
        merge13 = concatenate([conv1, up13], axis=3)
        conv13 = Conv2D(16, 3, activation='relu', padding='same', kernel_initializer='he_normal')(merge13)
        conv13 = BatchNormalization()(conv13)
        conv13 = Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv13)
        conv13 = BatchNormalization()(conv13)

        conv13 = Conv2D(1, 1, activation='sigmoid')(conv13)

        model = Model(input=inputs, output=conv13)
        print(model.summary())
        model.load_weights("LYM_vfa/unet3.hdf5")
        # model.compile(optimizer=Adam(lr=1e-4), loss='binary_crossentropy', metrics=['accuracy'])
        model.compile(optimizer = Adam (lr=1e-4), loss = dice_coef_loss, metrics = [f1_score])

        return model

    def train(self):

        print("loading data")
        imgs_train, imgs_mask_train, imgs_test = self.load_data()

        print("loading data done")
        model = self.get_DilaLab()
        print("got DilaLab")
        # model_checkpoint = ModelCheckpoint('LYM_vfa/DilaLab-{}'.format(datetime.now().strftime('%Y-%m-%d-%H-%M'))+'-{epoch:02d}-{val_f1_score:.2f}.hdf5', monitor='loss',verbose=1, save_best_only=True)
        model_checkpoint = ModelCheckpoint('LYM_vfa/unet31.hdf5', monitor='loss',verbose=1, save_best_only=True)
        print('Fitting model...')
        print(imgs_train.shape,imgs_mask_train.shape)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=1, min_lr=1e-5)
        hist = model.fit(imgs_train, imgs_mask_train, batch_size=1, nb_epoch=30, verbose=1,validation_split=0.2, shuffle=True, callbacks=[model_checkpoint,reduce_lr])
        with open('LYM_vfa/log_2.txt', 'w') as f:
            f.write(str(hist.history)+'\n')
        print('predict test data')
        print(imgs_test.shape)
        imgs_mask_test = model.predict(imgs_test, batch_size=1, verbose=1)
        np.save('LYM_vfa\\results\\imgs_mask_test_pred.npy', imgs_mask_test)

    def save_img(self):
        print("array to image")
        imgs = np.load('LYM_vfa\\results\\imgs_mask_test_pred.npy')
        for i in range(imgs.shape[0]):
            img = imgs[i]
            img = array_to_img(img)
            img.save("LYM_vfa\\results\\%d.jpg"%(i))

from datetime import datetime
if __name__ == '__main__':
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"



    start = datetime.now()
    myDilaLab =myDilaLab()
    myDilaLab.train()

    stop = datetime.now()
    # print(stop - start)
    print('Training time cost: %0.2f(min).' % ((stop - start) / 60))







