"""A build_model.py létrehoz egy hdf5 fájlt. Használd a predictet,
hogy a modellen kiértékelj képeket.
"""
import tensorflow as tf
from PIL import Image
import numpy as np
from skimage import transform
import pathlib

path = pathlib.Path(__file__).parent
model = tf.keras.models.load_model(str(path / 'my_model.h5'))

def load(filename):
    np_image = Image.open(filename)
    np_image = np.array(np_image).astype('float32')/255
    np_image = transform.resize(np_image, (256, 256, 3))
    np_image = np.expand_dims(np_image, axis=0)
    return np_image


def predict(filename):
    image = load(filename)
    return model.predict(image)


if __name__ == "__main__":
    import pathlib
    for img in pathlib.Path("test_images").iterdir():
        print(str(img))
        print(predict(str(img)))