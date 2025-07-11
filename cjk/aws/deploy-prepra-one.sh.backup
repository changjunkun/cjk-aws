#!/bin/bash

# 检查是否提供了参数
if [ -z "$1" ]; then
    echo "No parameter provided. Exiting..."
    exit 1
fi

# 获取传递的参数
MAP=$1

# 输出接收到的参数
echo "Received parameter: $MAP"

# 执行部署逻辑（根据参数执行不同操作）
echo "Deploying with MAP=$MAP"

# git clone https://github.com/changjunkun/aws.git
#cd /root/aws

# 升级pip，npm版本为 pip:24.3.1  npm：11.0.0

npm install -g npm@11.0.0 --force
# 检查npm是否升级到11.0.0版本
npm --version 

# 安装cdk工具
sudo npm install -g aws-cdk

python3 -m venv .venv
source .venv/bin/activate
/root/aws/.venv/bin/python3 -m pip install --upgrade pip
pip --version

pip install -r requirements.txt

# 若是部署某AWS所有打开的区域
chmod +x *.sh
./deploy-one.sh $MAP

