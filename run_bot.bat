@echo off
title Telegram Bot - Warehouse
:: Переходим в папку, где лежит сам bat-файл
cd /d "%~dp0"
echo Starting your Telegram Bot...
:: Запускаем python и указываем файл
python main.py
pause