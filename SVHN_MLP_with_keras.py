# %%
from keras.utils.data_utils import get_file
from scipy import io
import numpy as np
import keras
import os

from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D

# %%
batch_size = 32
num_classes = 10
epochs = 1
num_predictions = 20
save_dir = os.path.join(os.getcwd(), 'saved_models')
train_path = os.path.join(os.getcwd(), 'data\\train_32x32.mat')
test_path = os.path.join(os.getcwd(), 'data\\test_32x32.mat')
model_name = 'keras_svhn_trained_model.h5'
data_augmentation = True


# %%
def loadmat(filename):
    # load SVHN dataset
    mat = io.loadmat(filename)
    # the key to image data is 'X', the image label key is 'y'
    data = mat['X']
    label = mat['y']
    rows = data.shape[0]
    cols = data.shape[1]
    channels = data.shape[2]
    # in matlab data, the image index is the last index
    # in keras, the image index is the first index so
    # perform transpose for the last index
    data = np.transpose(data, (3, 0, 1, 2))
    return data, label


# %%
print(train_path)
# %%
get_file(train_path,
         origin='http://ufldl.stanford.edu/housenumbers/train_32x32.mat')
get_file(test_path,
         'http://ufldl.stanford.edu/housenumbers/test_32x32.mat')
train_data, train_labels = loadmat(train_path)
train_labels = train_labels - 1
test_data, test_labels = loadmat(test_path)
test_labels = test_labels - 1
# %%
print(train_labels)
# %%
train_labels_vector = keras.utils.to_categorical(train_labels, num_classes)
test_labels_vector = keras.utils.to_categorical(test_labels, num_classes)

# %%
print('train shape:', train_data.shape)
print(train_data.shape[0], 'train samples')
print(test_data.shape[0], 'test samples')

model = Sequential()
model.add(Flatten(input_shape=train_data.shape[1:]))
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

# initiate RMSprop optimizer
opt = keras.optimizers.rmsprop(lr=0.0001, decay=1e-6)

# Let's train the model using RMSprop
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

train_data = train_data.astype('float32')
test_data = test_data.astype('float32')
train_data /= 255
test_data /= 255

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(train_data, train_labels_vector,
              batch_size=batch_size,
              epochs=epochs,
              validation_data=(test_data, test_labels_vector),
              shuffle=True)
else:
    print('Using real-time data augmentation.')
    # This will do preprocessing and realtime data augmentation:
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        zca_epsilon=1e-06,  # epsilon for ZCA whitening
        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
        # randomly shift images horizontally (fraction of total width)
        width_shift_range=0.1,
        # randomly shift images vertically (fraction of total height)
        height_shift_range=0.1,
        shear_range=0.,  # set range for random shear
        zoom_range=0.,  # set range for random zoom
        channel_shift_range=0.,  # set range for random channel shifts
        # set mode for filling points outside the input boundaries
        fill_mode='nearest',
        cval=0.,  # value used for fill_mode = "constant"
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False,  # randomly flip images
        # set rescaling factor (applied before any other transformation)
        rescale=None,
        # set function that will be applied on each input
        preprocessing_function=None,
        # image data format, either "channels_first" or "channels_last"
        data_format=None,
        # fraction of images reserved for validation (strictly between 0 and 1)
        validation_split=0.0)

    # Compute quantities required for feature-wise normalization
    # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(train_data)

    print(model.summary())

    # Fit the model on the batches generated by datagen.flow().
    model.fit_generator(datagen.flow(train_data, train_labels_vector,
                                     batch_size=batch_size),
                        epochs=epochs,
                        validation_data=(test_data, test_labels_vector),
                        workers=4, steps_per_epoch=20)

# Save model and weights
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

# Score trained model.
scores = model.evaluate(test_data, test_labels_vector, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])
