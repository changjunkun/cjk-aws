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
#regions='af-south-1 ap-south-2 ap-southeast-4 ap-south-1 ap-southeast-7 ca-west-1 eu-south-1 eu-south-2 eu-central-2 mx-central-1 me-south-1 me-central-1 il-central-1'
regions='eu-central-1'
# 循环遍历每个区域
for region in $regions; do
    echo "Deploying $tag to region: $region"

    # 导出 CDK_REGION 环境变量
    export CDK_REGION=$region
    cdk bootstrap --region $region
    cdk deploy --require-approval never --parameters tags="{\"map-migrated\":\"$tag\"}" --region $region

    echo "Deployment completed for region: $region"
    echo ""
done

aws s3 ls | grep cdk | awk '{print $3}' | while read bucket_name; do
    # 2. 删除存储桶中的所有内容，包括版本化对象
    echo "Deleting contents of bucket: s3://$bucket_name"

    # Delete all versions of objects in the bucket
    aws s3api list-object-versions --bucket $bucket_name --query "Versions[].{Key:Key,VersionId:VersionId}" --output text | \
    while read key version_id; do
        aws s3api delete-object --bucket $bucket_name --key "$key" --version-id "$version_id"
    done

    # Delete all delete markers (if any)
    aws s3api list-object-versions --bucket $bucket_name --query "DeleteMarkers[].{Key:Key,VersionId:VersionId}" --output text | \
    while read key version_id; do
        aws s3api delete-object --bucket $bucket_name --key "$key" --version-id "$version_id"
    done

    # 3. 强制删除存储桶
    echo "Deleting bucket: s3://$bucket_name"
    aws s3 rb s3://$bucket_name --force
done
