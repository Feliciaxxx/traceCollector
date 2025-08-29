# Final Collector - 微服务测试版本

## 🎉 成功构建完成！

您的最终版本 OpenTelemetry Collector 已经准备就绪，可以进行微服务测试了！

## 📡 连接信息

- **gRPC 端点**: `localhost:4325`
- **HTTP 端点**: `localhost:4326`

## 🔧 配置详情

### 当前优化配置:
- **GroupByTrace**: 2秒等待时间，1000条缓冲
- **TailSampling**: 
  - 采样率: 100% (确保测试阶段不丢数据)
  - 缓冲区: 5条 (快速触发采样)
  - 决策等待: 1秒
  - 历史池: 10条
  - 组合数: 2

## 🚀 启动方式

```bash
cd "c:\Users\Lenovo\final-collector"
.\final-collector.exe --config=config.yml
```

## 🔄 数据流管道

```
微服务 → OTLP Receiver → TailSampling Processor → Debug Exporter
```

## 📊 微服务集成

请在您的微服务中配置 OpenTelemetry 导出器指向:

### Go/Java/Python 应用配置:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4326
```

### 或者使用 gRPC:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4325
```

## 🔍 监控和调试

Collector 会输出详细的调试信息，包括:
- 收到的 trace 数量
- 采样决策过程
- 遗传算法优化日志
- 缓冲区状态

## ✅ 测试建议

1. **启动 Collector** (已运行)
2. **发送测试数据**: 从您的微服务发送一些 traces
3. **观察日志**: 查看 Collector 控制台输出的处理信息
4. **验证采样**: 确认 trace 数据正常流动

## 🛠️ 问题排查

如果遇到端口冲突，可以修改 `config.yml` 中的端口号:
```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: "0.0.0.0:YOUR_HTTP_PORT"
      grpc:
        endpoint: "0.0.0.0:YOUR_GRPC_PORT"
```

## 📈 生产环境调整

测试完成后，可以调整以下配置用于生产:
- 将采样率调整为合适的值 (如 0.1 = 10%)
- 增加缓冲区大小 (如 1000)
- 调整决策等待时间

祝测试顺利！🎯
