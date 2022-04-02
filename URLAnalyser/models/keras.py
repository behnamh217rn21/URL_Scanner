import os
from keras.models import load_model


def save_model(model, filename, path=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data", "models")):
    model.save(os.path.join(path, filename))

def load_model(filename, path=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data", "models")):
    return load_model(os.path.join(path, filename))
