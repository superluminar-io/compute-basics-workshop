from os import path

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct


class EcsWorkshopStack(Stack):

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
        # Add endpoints if you want to deploy to a private subnet
        vpc.add_interface_endpoint(
            "ECS",
            service=ec2.InterfaceVpcEndpointAwsService.ECS,
        )
        vpc.add_interface_endpoint(
            "ECR",
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
        )
        vpc.add_interface_endpoint(
            "ECRDocker",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
        )
        vpc.add_interface_endpoint(
            "CloudWatchLogs",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        )
        vpc.add_gateway_endpoint(
            "S3",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        asset = ecr_assets.DockerImageAsset(
            self,
            "ECRAsset",
            directory=path.join(path.dirname(__file__), "..", "docker")
        )

        CfnOutput(
            self,
            "ECRRepository",
            value=asset.repository.repository_uri_for_tag(asset.image_uri),
        )

        cluster = ecs.Cluster(
            self,
            "WorkshopCluster",
            vpc=vpc,
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            "WorkshopTask",
            cpu=256,
            memory_limit_mib=512,
        )
        task_definition.add_container(
            "WorkshopContainer",
            image=ecs.ContainerImage.from_docker_image_asset(asset),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="WorkshopContainer",
            ),
        )

        nginx_task_definition = ecs.FargateTaskDefinition(
            self,
            "NginxTask",
            cpu=256,
            memory_limit_mib=512,
        )
        nginx_container = nginx_task_definition.add_container(
            "NginxContainer",
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/nginx/nginx:stable"
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="NginxContainer",
            ),
        )
        nginx_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
            )
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "WorkshopService",
            cluster=cluster,
            task_definition=nginx_task_definition,
            desired_count=2,
            public_load_balancer=True,
            listener_port=80,
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            assign_public_ip=True,
        )

        service.service.auto_scale_task_count(
            max_capacity=4,
            min_capacity=2,
        ).scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
        )
