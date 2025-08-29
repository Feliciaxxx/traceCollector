@echo off
echo ========================================
echo    启动 Final Collector 微服务测试版
echo ========================================
echo.
echo 配置信息:
echo - 监听端口: 4317 (gRPC), 4318 (HTTP)
echo - GroupByTrace: 2s 等待时间
echo - TailSampling: 90%% 采样率, 50条缓冲
echo - 管道: OTLP -^> GroupByTrace -^> TailSampling -^> Debug
echo.
echo 准备启动...
echo.

go run main.go

echo.
echo ========================================
echo    Collector 已停止
echo ========================================
pause
