"""
やること
・展開時、zip化されたディレクトリの中にあるディレクトリやcvv,sqlの表示
・複数中身がある際の表示

zipを展開するコード
ディレクトリにも対応済み

dir:ディレクトリのこと
"""

import os
import zipfile
from tkinter import *
from tkinter import filedialog


current_dir = os.path.dirname(__file__)
targets = filedialog.askopenfiles(initialdir=current_dir, filetypes=[('zip file', 'zip')])

for target in targets:
    target_folder = os.path.basename(target.name).split('.')[0]
    with zipfile.ZipFile(target.name, 'r') as zf:
        for info in zf.infolist():

            if info.is_dir():
                continue

            file_path = os.path.join(current_dir,target_folder,info.filename)
            os.makedirs(os.path.dirname(file_path),exist_ok=True)
            with zf.open(info) as src, open(file_path, 'wb') as dst:
                dst.write(src.read())
                


