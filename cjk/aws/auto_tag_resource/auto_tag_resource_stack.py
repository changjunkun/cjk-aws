from aws_cdk import (
    CfnParameter,
    Duration,
    Stack,
    Aws,
    aws_iam as _iam,
    aws_events as _events,
    aws_events_targets as _targets,
    aws_lambda as _lambda
)
from constructs import Construct

class AutoTagResourceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "AutoTagResourceQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        # set parameters
        tags = CfnParameter(self, "tags", type="String", description="tag name and value with json format.")
        identityRecording = CfnParameter(self, "identityRecording", type="String", default="false", description="Defines if the tool records the requester identity as a tag.")

        # create role for lambda function
        lambda_role = _iam.Role(self, "lambda_role",
            role_name = f"resource-tagging-role-{Aws.REGION}",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"))

        #lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        lambda_role.add_to_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=["*"],
            actions=["dynamodb:TagResource", "dynamodb:DescribeTable", "lambda:TagResource", "lambda:ListTags", "s3:GetBucketTagging", "s3:PutBucketTagging", 
            "ec2:CreateTags", "ec2:DescribeNatGateways", "ec2:DescribeInternetGateways", "ec2:DescribeVolumes", "rds:AddTagsToResource", "rds:DescribeDBInstances",
            "sns:TagResource", "sqs:ListQueueTags", "sqs:TagQueue", "es:AddTags", "kms:ListResourceTags", "kms:TagResource", "elasticfilesystem:TagResource", 
            "elasticfilesystem:CreateTags", "elasticfilesystem:DescribeTags", "eks:TagResource", "eks:DescribeCluster", "eks:DescribeNodegroup", "dms:DescribeReplicationInstances", "dms:AddTagsToResource", "elasticloadbalancing:AddTags","tag:getResources", "tag:getTagKeys", "tag:getTagValues", "tag:TagResources", "tag:UntagResources", "cloudformation:DescribeStacks", 
            "cloudformation:ListStackResources", "elasticache:DescribeReplicationGroups", "elasticache:DescribeCacheClusters", "elasticache:AddTagsToResource", "elasticache:*", "resource-groups:*", "GameLift:TagResource", "kafka:TagResource", "kafka:UntagResource", "kafka:List*", "docdb:ListTagsForResource", "docdb:AddTagsToResource", "docdb:RemoveTagsFromResource", "workspaces:TagResource", "workspaces:UntagResource", "workspaces:DescribeWorkspaces", "workspaces:DescribeTags", "route53:ListTagsForResource", "route53:TagResource", "route53:UntagResource", "kafka-cluster:Describe*", "route53resolver:TagResource", "workspaces:*", "ds:*"]
        ))

        # create lambda function
        tagging_function = _lambda.Function(self, "resource_tagging_automation_function",
                                    runtime=_lambda.Runtime.PYTHON_3_10,
                                    memory_size=128,
                                    timeout=Duration.seconds(600),
                                    handler="lambda-handler.main",
                                    code=_lambda.Code.from_asset("./lambda"),
                                    function_name="resource-tagging-automation-function",
                                    role=lambda_role,
                                    environment={
                                        "tags": tags.value_as_string,
                                        "identityRecording": identityRecording.value_as_string
                                    }
                        )

        _eventRule = _events.Rule(self, "resource-tagging-automation-rule",
                        event_pattern=_events.EventPattern(
                            source=["aws.ec2", "aws.elasticloadbalancing", "aws.rds", "aws.lambda", "aws.s3", "aws.dynamodb", "aws.elasticfilesystem", "aws.es", "aws.sqs", "aws.sns", "aws.kms", "aws.dms", "aws.kafka", "aws.route53", "aws.workspaces", "aws.elasticache", "aws.eks"],
                            detail_type=["AWS API Call via CloudTrail"],
                            detail={
                                "eventSource": ["ec2.amazonaws.com", "elasticloadbalancing.amazonaws.com", "s3.amazonaws.com", "rds.amazonaws.com", "lambda.amazonaws.com", "dynamodb.amazonaws.com", "elasticfilesystem.amazonaws.com", "es.amazonaws.com", "sqs.amazonaws.com", "sns.amazonaws.com", "kms.amazonaws.com", "dms.amazonaws.com", "kafka.amazonaws.com", "route53.amazonaws.com", "workspaces.amazonaws.com", "elasticache.amazonaws.com", "eks.amazonaws.com"],
                                "eventName": ["RunInstances", "CreateFunction20150331", "CreateBucket", "CreateDBInstance", "CreateTable", "CreateVolume", "CreateLoadBalancer", "CreateMountTarget", "CreateDomain", "CreateQueue", "CreateTopic", "CreateKey", "CreateReplicationGroup", "CreateCacheCluster", "ModifyReplicationGroupShardConfiguration", "CreateFleet", "CreateDirectoryUserForConsole", "CreateVpc", "CreateRoute", "CreateHostedZone", "CreateInternetGateway", "CreateNatGateway", "AllocateAddress", "CreateVpcEndpoint", "CreateTransitGateway", "CreateReplicationInstance", "CreateCluster", "CreateClusterV2", "CreateServerlessKafkaCluster", "UpdateServerlessKafkaCluster", "CreateTags", "CreateServerlessCluster", "ModifyCluster", "DeregisterWorkspaceDirectory", "CreateDirectory", "CreateWorkspaces", "ChangeResourceRecordSets", "CreateServerlessCache", "CreateCacheCluster", "CreateReplicationGroup", "CopyServerlessCacheSnapshot", "CopySnapshot", "CreateCacheParameterGroup", "CreateCacheSecurityGroup", "CreateCacheSubnetGroup", "CreateServerlessCacheSnapshot", "CreateSnapshot", "CreateUserGroup", "CreateUser", "PurchaseReservedCacheNodesOffering", "CreateRecordSet", "CreateInboundEndpoint", "CreateHostedZone", "UpdateCluster", "CreateStream", "UpdateStream", "CreateWorkspace", "CreateVpcPeeringConnection", "CreateTags", "CreateCacheParameterGroup", "CreateNetworkInterface"]
                            }
                        )
                    )

        _eventRule.add_target(_targets.LambdaFunction(tagging_function, retry_attempts=2))
