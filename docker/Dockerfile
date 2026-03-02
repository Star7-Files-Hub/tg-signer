FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && apt-get install -y gcc && \
    mkdir -p build && \
    pip wheel -w build tgcrypto

FROM python:3.12-slim

ARG TZ=Asia/Shanghai
ENV TZ=${TZ}
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=builder /build/*.whl /tmp/

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 语法已修复：续行符正确，同时安装 tgcrypto 和 gui
RUN pip install /tmp/*.whl && \
    pip install -U "tg-signer[tgcrypto,gui]"

WORKDIR /opt/tg-signer
VOLUME /opt/tg-signer

# 官方 WebUI 默认端口是 8080
EXPOSE 8080

# 官方正确启动命令（可在 compose 中覆盖）
CMD ["tg-signer", "webgui", "--auth-code", "averycomplexcode", "--host", "0.0.0.0", "--port", "8080"]