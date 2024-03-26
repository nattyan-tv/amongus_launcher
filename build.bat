.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean --noconfirm --onefile --windowed "main.py" --name "Among Us"
deactivate
