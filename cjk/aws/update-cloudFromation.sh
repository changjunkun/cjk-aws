
#!/bin/bash
regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
#指定region
#regions='us-east-1'
cat > update-tags.json <<EOF
[
  {
    "ParameterKey": "tags",
    "ParameterValue": "{\"map-migrated\":\"mig2RADXB0QE3\"}"
  }
]
EOF
# 循环遍历每个区域
for region in $regions; do
 
# 获取当前标签

# 更新单个堆栈
   aws cloudformation update-stack   --stack-name AutoTagResourceStack   --use-previous-template   --parameters file://update-tags.json   --capabilities CAPABILITY_NAMED_IAM --region $region
   echo "Stacks update in region: $region"
done

