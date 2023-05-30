from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
    aws_secretsmanager as secret,
)
from constructs import Construct


class RdsWorkshopRestoreStack(Stack):

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

        mysql_cluster = rds.DatabaseClusterFromSnapshot(
            self,
            "WorkshopDatabaseFromSnapshot",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_01_0
            ),
            instance_props=rds.InstanceProps(
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                vpc=vpc
            ),
            default_database_name="workshop",
            snapshot_identifier="arn:aws:rds:eu-west-1:084274240787:cluster-snapshot:test-snapshot-9-58",  # noqa: E501
        )

        ecs_cluster = ecs.Cluster(
            self,
            "WorkshopCluster",
            vpc=vpc,
        )

        phpmyadmin_task_definition = ecs.FargateTaskDefinition(
            self,
            "PhpMyAdminTask",
            cpu=256,
            memory_limit_mib=512,
        )

        mysql_secret = secret.Secret.from_secret_name_v2(
            self,
            "WorkshopDatabaseSecret",
            mysql_cluster.secret.secret_name,
        )

        phpmyadmin_container = phpmyadmin_task_definition.add_container(
            "PhpMyAdminContainer",
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/bitnami/phpmyadmin:latest"
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="phpmyadmin",
            ),
            secrets={
                "DATABASE_HOST": ecs.Secret.from_secrets_manager(
                    mysql_secret,
                    field="host",
                ),
                "DATABASE_USER": ecs.Secret.from_secrets_manager(
                    mysql_secret,
                    field="username",
                ),
                "DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                    mysql_secret,
                    field="password",
                ),
            },
            environment={
                "DATABASE_ENABLE_SSL": "yes",
            }
        )
        phpmyadmin_container.add_port_mappings(
            ecs.PortMapping(
                container_port=8080,
            )
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "PhpMyAdminService",
            cluster=ecs_cluster,
            task_definition=phpmyadmin_task_definition,
            desired_count=1,
            public_load_balancer=True,
            listener_port=80,
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            assign_public_ip=True,
        )

        mysql_cluster.connections.allow_default_port_from(service.service)
