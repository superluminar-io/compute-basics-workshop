from aws_cdk import (
    Stack,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class WorkshopStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "WorkshopVPC",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=20
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=20
                )
            ]
        )

        alb = elbv2.ApplicationLoadBalancer(
            self,
            "WorkshopALB",
            vpc=vpc,
            internet_facing=True,
        )
        listener = alb.add_listener(
            "WorkshopListener",
            port=80,
            open=True,
        )
        nginx_target_group = listener.add_targets(
            "WorkshopTarget",
            port=80,
        )

        nginx_autscaling_group = autoscaling.AutoScalingGroup(
            self,
            "WorkshopASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            allow_all_outbound=False,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage().lookup(
                name="bitnami-nginx-1.23.3-22-r21-linux-debian-11-x86_64-hvm-ebs-nami",  # noqa: E501
            ),
            min_capacity=1,
            max_capacity=2,
        )
        nginx_autscaling_group.scale_on_cpu_utilization(
            "WorkshopScaleOnCPU",
            target_utilization_percent=50,
        )
        nginx_autscaling_group.attach_to_application_target_group(
            nginx_target_group
        )

        nginx_autscaling_group.connections.allow_from(
            alb, ec2.Port.tcp(80), "Allow inbound HTTP access from ALB"
        )
