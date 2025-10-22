@echo off
REM Navigate to Django project folder
cd "C:\Users\AL MUZANY\Documents\Development\Back-end\Django\project_egaz"

REM Run the Django management command and save output
"C:\Users\AL MUZANY\AppData\Local\Programs\Python\Python312\python.exe" manage.py update_payments >> "C:\Users\AL MUZANY\Documents\update_payments.log" 2>&1
