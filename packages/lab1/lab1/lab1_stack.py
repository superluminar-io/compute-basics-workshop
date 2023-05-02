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
            max_azs=1,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=17
                )
            ]
        )
