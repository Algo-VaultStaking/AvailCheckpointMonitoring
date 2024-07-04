# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster
WORKDIR /app

RUN apt-get update && \
  apt-get install -y \
  nano \
  tmux \
  wget \
  curl \
  git \
  gcc \
  libc6-dev \
  make \
  cmake \
  libssl-dev \
  libmariadb3 \
  libmariadb-dev \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install mariadb==1.0.9
RUN pip3 install discord
RUN pip3 install web3
RUN pip3 install configparser

COPY . .

RUN chmod a+x run_all_python.sh
CMD ["./run_all_python.sh"]
#ENTRYPOINT ["./run_all.sh"]

