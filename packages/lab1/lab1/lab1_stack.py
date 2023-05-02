from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class Lab1Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ec2.Vpc(
            self,
            "Lab1VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
        )
