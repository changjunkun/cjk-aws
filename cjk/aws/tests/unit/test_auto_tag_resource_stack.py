import aws_cdk as core
import aws_cdk.assertions as assertions

from auto_tag_resource.auto_tag_resource_stack import AutoTagResourceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in auto_tag_resource/auto_tag_resource_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AutoTagResourceStack(app, "auto-tag-resource")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
