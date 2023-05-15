from aws_cdk import (
    Size,
    Stack,
    aws_batch_alpha as batch,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
)
from constructs import Construct


class BatchWorkshopStack(Stack):

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
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=20
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=20
                )
            ]
        )

        compute_env = batch.ManagedEc2EcsComputeEnvironment(
            self,
            "BatchComputeEnvironment",
            vpc=vpc,
            spot=True,
            spot_bid_percentage=100,
        )

        job_queue = batch.JobQueue(
            self,
            "BatchJobQueue",
            compute_environments=[
                batch.OrderedComputeEnvironment(
                    compute_environment=compute_env,
                    order=1
                )
            ]
        )

        job_definition = batch.EcsJobDefinition(
            self,
            "BatchJobDefinition",
            container=batch.EcsEc2ContainerDefinition(
                self,
                "BatchContainerDefinition",
                image=ecs.ContainerImage.from_registry("amazonlinux"),
                command=["echo", "hello world"],
                memory=Size.mebibytes(512),
                cpu=1,
                logging=ecs.LogDriver.aws_logs(
                    stream_prefix="batch",
                    log_retention=logs.RetentionDays.ONE_WEEK
                )
            )
        )