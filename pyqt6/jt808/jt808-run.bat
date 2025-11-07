pyinstaller --onefile --windowed --name JT808BSJlParser.exe \
           --icon=assets/app.ico \
           --add-data "assets/*;assets" \
           --hidden-import tkinter \  # 确保弹窗功能可用
           --hidden-import pathlib \  # 显式包含pathlib
           --paths=src \         # 指定模块搜索路径
           jt808_ui.py