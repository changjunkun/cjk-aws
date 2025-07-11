#!/bin/bash

# 检查是否提供了参数
if [ -z "$1" ]; then
    echo "Tag:  <tag>"
    exit 1
fi

tag=$1
# 获取当前 AWS 账户的所有区域列表
#regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
#指定region
regions='us-east-1 us-west-2'
# 循环遍历每个区域
for region in $regions; do
    echo "Deploying $tag to region: $region"

    # 导出 CDK_REGION 环境变量
    export CDK_REGION=$region
    cdk bootstrap
    cdk deploy --require-approval never --parameters tags="{\"map-migrated\":\"$tag\"}"

    echo "Deployment completed for region: $region"
    echo ""
done

aws s3 ls |grep cdk |xarge aws s3 rm s3://$1 --recursive
