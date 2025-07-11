
#!/bin/bash
#regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
#指定region
regions='eu-west-1'
# 循环遍历每个区域
for region in $regions; do
  # 导出 CDK_REGION 环境变量
  export CDK_REGION=$region
  # 删除区域中的所有堆栈
   echo "Deleting stacks in region: $region"
   #
   # 获取所有已部署的CDK堆栈名称
   stacks=$(cdk list)
   for stack in $stacks; do
   # 删除每个堆栈
   echo "Deleting stack: $stack"
   cdk destroy --region $region --force $stack
   aws cloudformation delete-stack --stack-name CDKToolkit --region $region
   done
   echo "Stacks deleted in region: $region"
   echo ""
done

