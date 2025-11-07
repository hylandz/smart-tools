pyinstaller --onefile \
    --windowed \
    --name BSJ2929Parser_v1.0.0.exe \
    --icon=assets/icons29/app.ico \
    --add-data "assets/*;assets" \
    --hidden-import tkinter \
    --hidden-import pathlib \
    --paths=src \
    2929_ui.py


pyinstaller --clean --onefile --windowed --name BSJ2929Parser_v1.1.4.exe --icon=assets/icons/app.ico --hidden-import tkinter --paths=bsj2929 2929_ui.py