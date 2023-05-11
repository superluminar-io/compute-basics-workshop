import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_workshop.ecs_workshop_stack import EcsWorkshopStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ecs_workshop/ecs_workshop_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsWorkshopStack(app, "ecs-workshop")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
