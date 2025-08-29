# 使用一个稳定的 Go 版本
FROM golang:1.24-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

# 关键！将当前目录下的所有文件和文件夹（包括处理器代码）都复制到容器中
COPY . .

# 在容器内部安装 builder 并构建
RUN go install go.opentelemetry.io/collector/cmd/builder@latest
RUN /go/bin/builder --config=./builder-config.yaml

# ---- 运行环境 ----
FROM alpine:latest

WORKDIR /app

# 从构建阶段复制最终生成的可执行文件
# 注意：这里的名字来自 builder-config.yaml 中的 "dist.name"
COPY --from=builder /app/final-collector .
# 将您的配置文件也复制进去
COPY config.yml .

EXPOSE 4318
ENTRYPOINT ["/app/final-collector", "--config=/app/config.yml"]