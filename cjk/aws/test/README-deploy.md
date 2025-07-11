git clone https://github.com/xxxx/auto_tag_resource.git
cd auto_tag_resource
sudo npm install -g aws-cdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
#执⾏cdk deploy命令进⾏⼯具部署，注意map-migrated的标签值
./deploy.sh migGFMN2TSAJY
