import boto3
import os
import json
import time 

def check_nat_gateway_status(region, nat_gateway_id):
    """Polls the NAT Gateway status to check if it is in a 'available' state."""
    ec2_client = boto3.client('ec2', region_name=region)
    try:
        response = ec2_client.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])
        status = response['NatGateways'][0]['State']
        return status
    except Exception as e:
        print(f"Error checking NAT Gateway status: {e}")
        return None

def check_and_tag_resource(resource_arn, region, account_id):
    """Check if resource has tags."""
    resourcegroupstaggingapi = boto3.client('resourcegroupstaggingapi', region_name=region)
    try:
        # Check if the resource has tags
        response = resourcegroupstaggingapi.get_resources(
            ResourceARNList=[resource_arn]
        )

        if 'ResourceTagMappingList' in response and len(response['ResourceTagMappingList']) == 0:
            print(f"Resource {resource_arn} has no tags.")
        else:
            print(f"Resource {resource_arn} already has tags.")
    except Exception as e:
        print(f"Error checking or tagging resource {resource_arn}: {e}")



def aws_ec2(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    ec2ArnTemplate = 'arn:aws:ec2:@region@:@account@:instance/@instanceId@'
    volumeArnTemplate = 'arn:aws:ec2:@region@:@account@:volume/@volumeId@'
    resourceArnTemplate = 'arn:aws:ec2:@region@:@account@:resourceName/@resourceId@'
    
    if event['detail']['eventName'] == 'RunInstances':
        print("tagging for new EC2...")
        _instanceId = event['detail']['responseElements']['instancesSet']['items'][0]['instanceId']
        arnList.append(ec2ArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@instanceId@', _instanceId))

        ec2_resource = boto3.resource('ec2')
        _instance = ec2_resource.Instance(_instanceId)
        for volume in _instance.volumes.all():
            arnList.append(volumeArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@volumeId@', volume.id))

    elif event['detail']['eventName'] == 'CreateVolume':
        print("tagging for new EBS...")
        _volumeId = event['detail']['responseElements']['volumeId']
        arnList.append(volumeArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@volumeId@', _volumeId))
    elif event['detail']['eventName'] == 'CreateVpc':
        print("tagging for new VPC...")
        _vpcId = event['detail']['responseElements']['vpc']['vpcId']
        arnList.append(resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'vpc').replace('@resourceId@', _vpcId))
        
    elif event['detail']['eventName'] == 'CreateInternetGateway':
        print("tagging for new IGW...")
        _igwId = event['detail']['responseElements']['internetGateway']['internetGatewayId']
        arnList.append(resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'internet-gateway').replace('@resourceId@', _igwId))
        
    elif event['detail']['eventName'] == 'CreateNatGateway':
        print("Processing NAT Gateway creation...")
        _natgwResponse = event['detail']['responseElements'].get('CreateNatGatewayResponse', {})
        if 'natGateway' in _natgwResponse:
            _natgwId = _natgwResponse['natGateway'].get('natGatewayId')
            if _natgwId:
                print(f"Found NAT Gateway ID: {_natgwId}")
                arn = resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'natgateway').replace('@resourceId@', _natgwId)
                arnList.append(arn)
                check_and_tag_resource(arn, _region, _account)
            else:
                print("NAT Gateway ID not found immediately, polling for status...")
                retries = 5
                while retries > 0:
                    print(f"Retrying... {retries} attempts left.")
                    time.sleep(10)  # Delay before retrying
                    status = check_nat_gateway_status(_region, _natgwId)
                    if status == 'available':
                        print(f"NAT Gateway {natgwId} is now available.")
                        arn = resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'natgateway').replace('@resourceId@', _natgwId)
                        arnList.append(arn)
                        check_and_tag_resource(arn, _region, _account)
                        break
                    retries -= 1
                if retries == 0:
                    print(f"Failed to get NAT Gateway ID for {natgwId} after retries.")
        else:
            print("NAT Gateway creation failed or did not include the expected information.")
    elif event['detail']['eventName'] == 'AllocateAddress':
        print("tagging for new EIP...")
        _allocationId = event['detail']['responseElements']['allocationId']
        arnList.append(resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'natgateway').replace('@resourceId@', _allocationId))
        
    elif event['detail']['eventName'] == 'CreateVpcEndpoint':
        print("tagging for new VPC Endpoint...")
        _vpceId = event['detail']['responseElements']['CreateVpcEndpointResponse']['vpcEndpoint']['vpcEndpointId']
        arnList.append(resourceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('resourceName', 'vpc-endpoint').replace('@resourceId@', _vpceId))        
        
    elif event['detail']['eventName'] == 'CreateTransitGateway':
        print("tagging for new Transit Gateway...")
        arnList.append(event['detail']['responseElements']['CreateTransitGatewayResponse']['transitGateway']['transitGatewayArn'])
    
    
    return arnList

def aws_elasticloadbalancing(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateLoadBalancer':
        print("tagging for new LoadBalancer...")
        lbs = event['detail']['responseElements']
        for lb in lbs['loadBalancers']:
            arnList.append(lb['loadBalancerArn'])
        return arnList

def aws_rds(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateDBInstance':
        print("tagging for new RDS...")
        arnList.append(event['detail']['responseElements']['dBInstanceArn'])
        return arnList

def aws_dms(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateReplicationInstance':
        print("tagging for new DMS Instance...")
        arnList.append(event['detail']['responseElements']['replicationInstance']['replicationInstanceArn'])
        return arnList

def aws_elasticache(event):
    arn_list = []
    _account = event.get('account')
    _region = event.get('region')

    # Initialize ElastiCache client
    elasticache_client = boto3.client('elasticache', region_name=_region)

    # Retrieve tags from environment variable and parse JSON
    try:
        tags_env = os.getenv('tags', '{}')  # Retrieve 'tags' environment variable
        tags = json.loads(tags_env)  # Parse JSON string into Python dictionary
        tag_migrated_value = tags.get('map-migrated', 'DefaultMigration')  # Get 'map-migrated' value
    except json.JSONDecodeError as e:
        print(f"Error parsing 'tags' environment variable: {e}")
        tag_migrated_value = 'DefaultMigration'  # Default value

    # Check if the event contains 'detail' and necessary fields
    if 'detail' not in event:
        print("Event missing 'detail' field.")
        return arn_list

    # Handling CreateServerlessCache event
    if event['detail'].get('eventName') == 'CreateServerlessCache':
        print("Processing new ElastiCache serverless cache instance...")

        # Extract ARN and instance name from the event
        try:
            serverless_cache_arn = event['detail']['responseElements']['serverlessCache']['aRN']
            serverless_cache_name = event['detail']['responseElements']['serverlessCache']['serverlessCacheName']
            arn_list.append(serverless_cache_arn)
        except KeyError as e:
            print(f"Event missing expected fields: {e}")
            return arn_list

        # Set timeout and delay for waiting cache status to become 'available'
        timeout = int(os.getenv('CACHE_STATUS_TIMEOUT', 600))  # Timeout configurable via env var
        delay_interval = int(os.getenv('CACHE_STATUS_DELAY', 30))  # Retry delay interval

        # Wait for the cache instance to become 'available'
        try:
            start_time = time.time()

            while True:
                # Get the cache instance status
                response = elasticache_client.describe_serverless_caches(
                    ServerlessCacheName=serverless_cache_name
                )
                cache_status = response['ServerlessCaches'][0]['Status']

                if cache_status == 'available':
                    print(f"Cache instance {serverless_cache_name} is available, adding tags...")
                    elasticache_client.add_tags_to_resource(
                        ResourceName=serverless_cache_arn,
                        Tags=[{'Key': 'map-migrated', 'Value': tag_migrated_value}]
                    )
                    print(f"Successfully added tags to ElastiCache serverless cache instance: {serverless_cache_arn}")
                    break
                elif time.time() - start_time > timeout:
                    print(f"Timeout reached ({timeout} seconds), current status: {cache_status}")
                    break
                else:
                    print(f"Current status: {cache_status}. Retrying in {delay_interval} seconds...")
                    time.sleep(delay_interval)

        except Exception as e:
            print(f"Error adding tags to ElastiCache serverless cache instance: {e}")

    # Ensure this block is correctly indented
    elif event['detail'].get('eventName') in ['CreateReplicationGroup', 'CreateCacheCluster']:
        print("Handling ElastiCache replication group or cache cluster creation...")

        # Extract replication group or cache cluster information and process accordingly
        try:
            if event['detail']['eventName'] == 'CreateReplicationGroup':
                replication_group_arn = event['detail']['responseElements']['ReplicationGroup']['aRN']
                arn_list.append(replication_group_arn)
                # Further processing for CreateReplicationGroup can be added here
            elif event['detail']['eventName'] == 'CreateCacheCluster':
                cache_cluster_arn = event['detail']['responseElements']['CacheCluster']['aRN']
                arn_list.append(cache_cluster_arn)
                # Further processing for CreateCacheCluster can be added here

            # Add tags if needed
            # Assuming you want to add the same tag for these events as well:
            for arn in arn_list:
                elasticache_client.add_tags_to_resource(
                    ResourceName=arn,
                    Tags=[{'Key': 'map-migrated', 'Value': tag_migrated_value}]
                )
                print(f"Successfully added tags to ElastiCache resource: {arn}")

        except KeyError as e:
            print(f"Event missing expected fields for replication group or cache cluster: {e}")
            return arn_list
        except Exception as e:
            print(f"Error handling ElastiCache replication group or cache cluster creation: {e}")



    
    # 处理 CreateReplicationGroup 或 CreateCacheCluster 事件（传统类型集群）
    elif event['detail']['eventName'] in ['CreateReplicationGroup', 'CreateCacheCluster']:
        print(f"处理新的 ElastiCache 集群: {event['detail']['eventName']}")

        if event['detail']['eventName'] == 'CreateReplicationGroup':
            _replicationGroupId = event['detail']['responseElements']['replicationGroupId']
            arn = f"arn:aws:elasticache:{_region}:{_account}:replicationgroup:{_replicationGroupId}"
        else:
            _cacheClusterId = event['detail']['responseElements']['cacheClusterId']
            arn = f"arn:aws:elasticache:{_region}:{_account}:cluster:{_cacheClusterId}"

        arnList.append(arn)

        try:
            while True:
                if event['detail']['eventName'] == 'CreateReplicationGroup':
                    response = elasticache_client.describe_replication_groups(ReplicationGroupId=_replicationGroupId)
                    status = response['ReplicationGroups'][0]['Status']
                else:
                    response = elasticache_client.describe_cache_clusters(CacheClusterId=_cacheClusterId)
                    status = response['CacheClusters'][0]['CacheClusterStatus']

                if status == 'available':
                    print(f"集群状态为 available，准备添加标签...")

                    # 添加标签
                    elasticache_client.add_tags_to_resource(
                        ResourceName=arn,
                        Tags=[{'Key': 'map-migrated', 'Value': tag_migrated_value}]
                    )
                    print(f"成功为 ElastiCache 集群添加标签: {arn}")
                    break
                else:
                    print(f"当前状态为 {status}，等待 30 秒后重试...")
                    time.sleep(30)
        except Exception as e:
            print(f"为 ElastiCache 集群添加标签时出错: {e}")

        return arnList

    # 处理 CreateCacheSubnetGroup 事件（ElastiCache 子网组）
    elif event['detail']['eventName'] == 'CreateCacheSubnetGroup':
        print("处理新的 ElastiCache 子网组...")

        _subnetGroupArn = event['detail']['responseElements']['aRN']
        arnList.append(_subnetGroupArn)

        try:
            while True:
                response = elasticache_client.describe_cache_subnet_groups(
                    CacheSubnetGroupName=_subnetGroupArn.split(":")[-1]
                )
                subnet_group_status = response['CacheSubnetGroups'][0]['Status']

                if subnet_group_status == 'available':
                    print("子网组状态为 available，准备添加标签...")

                    # 添加标签
                    elasticache_client.add_tags_to_resource(
                        ResourceName=_subnetGroupArn,
                        Tags=[{'Key': 'map-migrated', 'Value': tag_migrated_value}]
                    )
                    print(f"成功为 ElastiCache 子网组添加标签: {_subnetGroupArn}")
                    break
                else:
                    print(f"当前状态为 {subnet_group_status}，等待 30 秒后重试...")
                    time.sleep(30)
        except Exception as e:
            print(f"为 ElastiCache 子网组添加标签时出错: {e}")

        return arnList

    print("未识别的事件类型，未处理任何资源。")
    return arnList
    
def aws_eks(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateCluster':
        print("tagging for new EKS Cluster...") 
        arnList.append(event['detail']['responseElements']['cluster']['arn'])
        return arnList

def aws_s3(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateBucket':
        print("tagging for new S3...")
        _bkcuetName = event['detail']['requestParameters']['bucketName']
        arnList.append('arn:aws:s3:::' + _bkcuetName)
        return arnList
        
def aws_lambda(event):
    arnList = []
    _exist1 = event['detail']['responseElements']
    _exist2 = event['detail']['eventName'] == 'CreateFunction20150331'
    if  _exist1!= None and _exist2:
        function_name = event['detail']['responseElements']['functionName']
        print('Functin name is :', function_name)
        arnList.append(event['detail']['responseElements']['functionArn'])
        return arnList

def aws_dynamodb(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateTable':
        table_name = event['detail']['responseElements']['tableDescription']['tableName']
        waiter = boto3.client('dynamodb').get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )
        arnList.append(event['detail']['responseElements']['tableDescription']['tableArn'])
        return arnList
        
def aws_kms(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateKey':
        arnList.append(event['detail']['responseElements']['keyMetadata']['arn'])
        return arnList
        
def aws_sns(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    snsArnTemplate = 'arn:aws:sns:@region@:@account@:@topicName@'
    if event['detail']['eventName'] == 'CreateTopic':
        print("tagging for new SNS...")
        _topicName = event['detail']['requestParameters']['name']
        arnList.append(snsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@topicName@', _topicName))
        return arnList
        
def aws_sqs(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    sqsArnTemplate = 'arn:aws:sqs:@region@:@account@:@queueName@'
    if event['detail']['eventName'] == 'CreateQueue':
        print("tagging for new SQS...")
        _queueName = event['detail']['requestParameters']['queueName']
        arnList.append(sqsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@queueName@', _queueName))
        return arnList
        
def aws_elasticfilesystem(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    efsArnTemplate = 'arn:aws:elasticfilesystem:@region@:@account@:file-system/@fileSystemId@'
    if event['detail']['eventName'] == 'CreateMountTarget':
        print("tagging for new efs...")
        _efsId = event['detail']['responseElements']['fileSystemId']
        arnList.append(efsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@fileSystemId@', _efsId))
        return arnList
        
def aws_es(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateDomain':
        print("tagging for new open search...")
        arnList.append(event['detail']['responseElements']['domainStatus']['aRN'])
        return arnList

def check_msk_cluster_status(region, cluster_arn):
    msk_client = boto3.client('kafka', region_name=region)
    try:
        response = msk_client.describe_cluster(ClusterArn=cluster_arn)
        status = response['ClusterInfo']['State']
        return status
    except Exception as e:
        print(f"Error checking MSK cluster status: {e}")
        return None

def aws_kafka(event):
    arnList = []

    # Get account and region details
    _account = os.getenv('AWS_ACCOUNT_ID')
    _region = os.getenv('AWS_REGION')

    # Initialize the MSK client
    msk_client = boto3.client('kafka', region_name=_region)

    # Check for MSK cluster creation event
    if event['detail']['eventName'] == 'CreateCluster':
        print("Processing new MSK Cluster...")

        # Extract the Cluster ARN
        try:
            cluster_arn = event['detail']['responseElements']['ClusterArn']
            arnList.append(cluster_arn)

            # Optionally, check the status of the cluster
            retries = 5
            while retries > 0:
                print(f"Retrying cluster status check... {retries} attempts left.")
                time.sleep(10)  # Delay before retrying
                status = check_msk_cluster_status(_region, cluster_arn)
                if status == 'ACTIVE':
                    print(f"MSK Cluster {cluster_arn} is now active.")
                    break
                retries -= 1
            if retries == 0:
                print(f"Failed to verify MSK Cluster status after retries.")
        except KeyError as e:
            print(f"Event missing expected fields for MSK cluster: {e}")
            return arnList
        except Exception as e:
            print(f"Error processing MSK cluster creation: {e}")
            return arnList

    return arnList


def aws_workspaces(event):
    # 创建 AWS 客户端
    wsclient = boto3.client('workspaces')  # WorkSpaces 客户端
    dsclient = boto3.client('ds')  # Directory Service 客户端
    resource_group_client = boto3.client('resourcegroupstaggingapi')  # 资源分组标记 API 客户端

    arnList = []  # 用于存储 ARN 列表
    _region = event['region']  # 获取事件中的 AWS 区域
    _account = event['account']  # 获取事件中的 AWS 账户 ID

    # 从环境变量获取标签信息
    try:
        tags_env = os.getenv('tags', '{}')
        tags = json.loads(tags_env)
        tag_key = 'map-migrated'
        tag_value = tags.get('map-migrated', 'DefaultMigration')
        print(f"从环境变量获取的标签: {tag_key}={tag_value}")
    except (json.JSONDecodeError, TypeError) as e:
        print(f"解析 'tags' 环境变量时出错: {e}")
        tag_key = 'map-migrated'
        tag_value = 'DefaultMigration'
    # 获取所有目录列表
    try:
        directories = []
        next_token = None

        while True:
            if next_token:
                response = dsclient.describe_directories(NextToken=next_token)
            else:
                response = dsclient.describe_directories()

            directories.extend(response['DirectoryDescriptions'])
            next_token = response.get('NextToken')
            if not next_token:
                break
    except Exception as e:
        print(f"获取 WorkSpaces 目录时出错: {e}")
        return {"statusCode": 500, "body": f"Error: {e}"}

    # 遍历所有目录，检查是否需要添加标签
    for directory in directories:
        directory_id = directory['DirectoryId']
        directory_name = directory['Name']
        print(f"正在检查目录 {directory_id} ({directory_name})")


        try:
            # 直接调用 ds.add_tags_to_resource API 为目录打标签
            response = dsclient.add_tags_to_resource(
                ResourceId=directory_id,
                Tags=[{'Key': tag_key, 'Value': tag_value}]  # 标签是列表格式
            )
            print(f"成功为目录 {directory_id} 添加标签: {response}")
        except Exception as e:
            print(f"为目录 {directory_id} 添加标签时出错: {e}")
    else:
        print("目录 ID 未找到，无法为目录添加标签")
   

    # 获取所有 WorkSpaces 实例
    try:
        workspaces = []
        next_token = None

        while True:
            if next_token:
                response = wsclient.describe_workspaces(NextToken=next_token)
            else:
                response = wsclient.describe_workspaces()

            workspaces.extend(response['Workspaces'])
            next_token = response.get('NextToken')
            if not next_token:
                break
    except Exception as e:
        print(f"获取 WorkSpaces 实例时出错: {e}")
        return {"statusCode": 500, "body": f"Error: {e}"}

    # 为 WorkSpaces 实例添加标签，进行重试
    for workspace in workspaces:
        workspace_id = workspace['WorkspaceId']
        print(f"正在处理 WorkSpace 实例 {workspace_id}")

        retries = 3
        success = False

        while retries > 0 and not success:
            try:
                # 获取当前 WorkSpace 标签
                response = wsclient.describe_tags(ResourceId=workspace_id)
                workspace_tags = response.get('TagList', [])
                print(f"WorkSpace {workspace_id} 当前标签: {workspace_tags}")

                # 检查标签是否已经存在
                if not any(tag['Key'] == tag_key for tag in workspace_tags):
                    wsclient.create_tags(
                        ResourceId=workspace_id,
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )
                    print(f"已为 WorkSpace {workspace_id} 添加 '{tag_key}' 标签")
                else:
                    print(f"WorkSpace {workspace_id} 已有 '{tag_key}' 标签")
                success = True
            except Exception as e:
                print(f"为 WorkSpace {workspace_id} 添加标签时出错: {e}")
                retries -= 1
                if retries > 0:
                    print(f"重试剩余次数: {retries}")
                    time.sleep(5)
                else:
                    print(f"WorkSpace {workspace_id} 标签添加失败，已达到最大重试次数")

    print("标签处理完成")
    return {"statusCode": 200, "body": "所有目录和 WorkSpaces 实例的标签处理完成"}


def main(event, context):
    print("Input event is: ")
    print(event)
    
    try:
        _method = event['source'].replace('.', "_")
        print(f"Processing source: {_method}")
        
        # Ensure the method exists before calling
        if _method in globals():
            resARNs = globals()[_method](event)
            print(f"Resource ARNs: {resARNs}")  # Debug print here

            if resARNs:  # Ensure ARN list is not empty
                _res_tags = json.loads(os.environ['tags'])
                boto3.client('resourcegroupstaggingapi').tag_resources(
                    ResourceARNList=resARNs,
                    Tags=_res_tags
                )
                return {
                    'statusCode': 200,
                    'body': json.dumps(f"Successfully tagged resources with source {event['source']}")
                }
            else:
                print("No ARNs found to tag.")
                return {
                    'statusCode': 400,
                    'body': json.dumps("No resources to tag.")
                }

        else:
            print(f"Method {event['source']} not found.")
            return {
                'statusCode': 400,
                'body': json.dumps("Invalid event source.")
            }

    except Exception as e:
        print(f"Error processing event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Internal error: {e}")
        }
