# syntax=docker/dockerfile:1

FROM python:3.11-slim-buster
WORKDIR /app

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y gnupg curl
RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 0xcbcb082a1bb943db
RUN curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | bash
RUN apt-get install -y \
  git \
  gcc \
  libc6-dev \
  make \
  cmake \
  libssl-dev \
  libmariadb3 \
  libmariadb-dev \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install mariadb==1.1.7
RUN pip3 install discord
RUN pip3 install slack-sdk
RUN pip3 install web3
RUN pip3 install configparser
RUN pip3 install substrate-interface

COPY . .

RUN chmod a+x run_all_python.sh
CMD ["./run_all_python.sh"]
#ENTRYPOINT ["./run_all.sh"]