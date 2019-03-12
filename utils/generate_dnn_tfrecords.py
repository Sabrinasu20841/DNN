import glob
from shutil import copyfile
import time
import os

src_data  ="./data/*.npy"
dest_data = "/tmp/dnn/"

if not os.path.exists(dest_data):
    os.mkdir(dest_data)
    print("Directory " , dest_data ,  " Created ")

files = glob.glob(src_data)
for file in files:
    copyfile(file, dest_data+ os.path.basename(file))
