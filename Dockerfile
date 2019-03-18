FROM alpine:latest

MAINTAINER T78

ENV LANG C.UTF-8
ENV TZ 'Asia/Shanghai'

RUN apk --update upgrade \
    && apk --update add tzdata ca-certificates \
       ffmpeg libmagic python3 \
       tiff libwebp freetype lcms2 openjpeg py3-olefile openblas
RUN apk add --no-cache build-base gcc python3-dev zlib-dev jpeg-dev libwebp-dev libffi-dev openssl-dev
RUN pip3 install numpy pillow pysocks ehforwarderbot efb-telegram-master efb-wechat-slave
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
