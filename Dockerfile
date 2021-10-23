FROM ubuntu

ENV TZ Asia/Tokyo

RUN apt-get update \
    && apt-get -y upgrade\
    && apt-get -y install tzdata \
    && cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get -y install locales python3 python3-pip \
    && locale-gen ja_JP.UTF-8 \
    && echo "export LANG=ja_JP.UTF-8" >> ~/.bashrc \
    && pip install boto3 requests_oauthlib schedule requests awscli \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*