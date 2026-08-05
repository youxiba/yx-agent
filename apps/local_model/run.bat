@echo off
REM Windows 启动脚本
set EMBEDDING_MODEL_NAME=%EMBEDDING_MODEL_NAME%
if "%EMBEDDING_MODEL_NAME%"=="" set EMBEDDING_MODEL_NAME=shibing624/text2vec-base-chinese
uvicorn app:app --host 0.0.0.0 --port %LOCAL_MODEL_PORT%
if "%LOCAL_MODEL_PORT%"=="" set LOCAL_MODEL_PORT=11636
uvicorn app:app --host 0.0.0.0 --port %LOCAL_MODEL_PORT%