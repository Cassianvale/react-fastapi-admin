@echo off
chcp 65001 >nul 2>&1
echo 正在结束所有Python进程...
taskkill /f /im python.exe >nul 2>&1
echo 已尝试终止Python进程

echo 正在删除数据库文件和migrations文件夹...
rmdir /s /q migrations 2>nul
del /f /q db.sqlite3 2>nul
del /f /q db.sqlite3-shm 2>nul
del /f /q db.sqlite3-wal 2>nul

echo 清理完成
pause 
