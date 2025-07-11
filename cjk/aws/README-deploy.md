#git clone https://github.com/xxxx/auto_tag_resource.git
#cd auto_tag_resource
#npm install -g aws-cdk
cd /root/cjk/aws
aws configure
python3.8 -m venv .venv
source .venv/bin/activate
nvm use 22 
./deploy.sh mig7D9IUWCW97
#执⾏cdk deploy命令进⾏⼯具部署，注意map-migrated的标签值
