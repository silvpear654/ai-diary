@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo 의존성 설치 중...
pip install -r requirements.txt

echo 실행 파일 빌드 중...
pyinstaller ^
    --onefile ^
    --name ai-diary ^
    --paths src ^
    --hidden-import google.genai ^
    --hidden-import google.generativeai ^
    --hidden-import cryptography.hazmat.primitives.ciphers ^
    --hidden-import cryptography.hazmat.backends.openssl ^
    --collect-all google.genai ^
    main.py

echo.
echo 빌드 완료!
echo 실행 파일 위치: dist\ai-diary.exe
echo.
echo 실행 방법:
echo    .env 파일을 dist\ 폴더에 복사한 후 dist\ai-diary.exe 실행
pause
