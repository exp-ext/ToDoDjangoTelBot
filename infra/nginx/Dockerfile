# Использование базового образа
FROM debian:bullseye-slim

# Установка необходимых пакетов для сборки
RUN apt-get update && \
    apt-get install -y build-essential cmake git wget libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev tar

# Установка Go (требуется для сборки BoringSSL)
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://dl.google.com/go/go1.20.linux-amd64.tar.gz && \
    tar -xvf go1.20.linux-amd64.tar.gz && \
    mv go /usr/local && \
    rm go1.20.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"

# Установка рабочей директории
WORKDIR /build

# Клонирование исходного кода BoringSSL
RUN git clone https://boringssl.googlesource.com/boringssl

# Сборка BoringSSL
WORKDIR /build/boringssl
RUN cmake . && make

# Копирование собранных файлов BoringSSL
RUN mkdir -p /usr/local/ssl && \
    cp -R include /usr/local/ssl/ && \
    mkdir -p /usr/local/ssl/lib && \
    cp ssl/libssl.a crypto/libcrypto.a /usr/local/ssl/lib/

# Клонирование исходного кода nginx
WORKDIR /build
RUN wget http://nginx.org/download/nginx-1.25.3.tar.gz && \
    tar zxvf nginx-1.25.3.tar.gz

# Сборка nginx с поддержкой BoringSSL
WORKDIR /build/nginx-1.25.3
RUN ./configure --with-http_ssl_module --with-cc-opt="-I /usr/local/ssl/include" --with-ld-opt="-L /usr/local/ssl/lib -lssl -lcrypto" && \
    make && make install

# Очистка неиспользуемых файлов
WORKDIR /
RUN rm -rf /build && \
    apt-get remove -y build-essential cmake git wget && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Настройка PATH
ENV PATH="/usr/local/nginx/sbin:${PATH}"

# Открытие портов
EXPOSE 80 443

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]