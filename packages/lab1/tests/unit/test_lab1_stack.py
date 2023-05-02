import aws_cdk as core
import aws_cdk.assertions as assertions

from lab1.lab1_stack import Lab1Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in lab1/lab1_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Lab1Stack(app, "lab1")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
