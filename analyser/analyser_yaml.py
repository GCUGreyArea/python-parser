import yaml
import os
import re

def load_yaml(FName):
    f = None
    try:
        f = open(FName)
        Yaml = yaml.load(f, Loader=yaml.FullLoader)
    except FileExistsError:
        raise ValueError(f"File {FName} does not exist")
    finally:
        if f is not None:
            f.close()

    return Yaml
