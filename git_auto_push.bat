@echo off
setlocal EnableDelayedExpansion

echo 🟡 Проверка статуса репозитория...
git status

echo 🟡 Добавление всех изменений...
git add .

set /p commitMessage=✏️ Введите сообщение коммита: 
if "%commitMessage%"=="" set commitMessage=Обновление проекта

echo 🟡 Создание коммита...
git commit -m "%commitMessage%"

echo 🟢 Отправка на GitHub...
git push origin main

echo ✅ Готово!
pause
