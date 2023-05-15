import aws_cdk as core
import aws_cdk.assertions as assertions

from batch_workshop.batch_workshop_stack import BatchWorkshopStack

# example tests. To run these tests, uncomment this file along with the example
# resource in batch_workshop/batch_workshop_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BatchWorkshopStack(app, "batch-workshop")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
