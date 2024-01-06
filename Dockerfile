# 此Dockerfile适用于“无本地模型”的迷你运行环境构建
# 如果需要使用chatglm等本地模型或者latex运行依赖，请参考 docker-compose.yml
# - 如何构建: 先修改 `config.py`， 然后 `docker build -t gpt-academic . `
# - 如何运行(Linux下): `docker run --rm -it --net=host gpt-academic `
# - 如何运行(其他操作系统，选择任意一个固定端口50923): `docker run --rm -it -e WEB_PORT=50923 -p 50923:50923 gpt-academic `
# FROM python:3.10

# https://mirrors.ustc.edu.cn/pypi/web/simple
# https://mirrors.aliyun.com/pypi/simple/
# # 非必要步骤，更换pip源 （以下三行，可以删除）
# RUN echo '[global]' > /etc/pip.conf && \
#     echo 'index-url = https://mirrors.ustc.edu.cn/pypi/web/simple/' >> /etc/pip.conf && \
#     echo 'trusted-host = mirrors.ustc.edu.cn' >> /etc/pip.conf
# 此Dockerfile适用于“无本地模型”的迷你运行环境构建
# 如果需要使用chatglm等本地模型或者latex运行依赖，请参考 docker-compose.yml
# - 如何构建: 先修改 `config.py`， 然后 `docker build -t gpt-academic . `
# - 如何运行(Linux下): `docker run --rm -it --net=host gpt-academic `
# - 如何运行(其他操作系统，选择任意一个固定端口50923): `docker run --rm -it -e WEB_PORT=50923 -p 50923:50923 gpt-academic `
FROM python:3.10

# https://mirrors.ustc.edu.cn/pypi/web/simple
# https://mirrors.aliyun.com/pypi/simple/
# # 非必要步骤，更换pip源 （以下三行，可以删除）
# RUN echo '[global]' > /etc/pip.conf && \
#     echo 'index-url = https://mirrors.ustc.edu.cn/pypi/web/simple/' >> /etc/pip.conf && \
#     echo 'trusted-host = mirrors.ustc.edu.cn' >> /etc/pip.conf



# # 进入工作路径（必要）
# WORKDIR /gpt


# # 安装大部分依赖，利用Docker缓存加速以后的构建 （以下三行，可以删除）
# COPY /nltk_data/ ../home/nltk_data
# RUN pip3 install setuptools --upgrade
# RUN pip3 install cmake protobuf 
# COPY requirements.txt ./
# COPY ./docs/gradio-3.32.6-py3-none-any.whl ./docs/gradio-3.32.6-py3-none-any.whl
# RUN pip3 install -r requirements.txt


# # install for rag
# RUN apt-get update && apt-get install -y poppler-utils libgl1-mesa-glx
# RUN pip3 install opencv-python-headless opencv-contrib-python

# # 装载项目文件，安装剩余依赖（必要）
# COPY . .

# # RUN apt install  -y

# # 非必要步骤，用于预热模块（可以删除）
# RUN python3  -c 'from check_proxy import warm_up_modules; warm_up_modules()'


# # 启动（必要）
# CMD ["python3", "-u", "main.py"]


# Use Python 3.10 slim image as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /gpt


# Use local mirrors for apt-get to speed up installation in China
RUN echo "deb http://mirrors.aliyun.com/debian/ buster main non-free contrib" > /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian/ buster main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security buster/updates main" >> /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian-security buster/updates main" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ buster-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian/ buster-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ buster-backports main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian/ buster-backports main non-free contrib" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y poppler-utils libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Optimize layer caching by copying only the requirements file first
COPY requirements.txt ./
COPY ./docs/gradio-3.32.6-py3-none-any.whl ./docs/gradio-3.32.6-py3-none-any.whl

# Upgrade setuptools and install dependencies
# Combined RUN commands to reduce layers
RUN pip install --no-cache-dir --upgrade setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Install OpenCV Python packages
RUN pip install --no-cache-dir opencv-contrib-python-headless

# Copy the rest of your application's code
COPY . .

# Pre-warming step (optional, can be removed to reduce build time)
# RUN python -c 'from check_proxy import warm_up_modules; warm_up_modules()'

# Define the command to run your app
CMD ["python", "-u", "main.py"]
