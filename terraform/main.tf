resource "aws_s3_bucket" "my_s3_bucket"{
    bucket = "my-s3-test-bucket02678"

    tags = {
    Name = "My bucket"
    Enviroment ="Dev"
}
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "my-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = element(["us-east-1a", "us-east-1b", "us-east-1c"], count.index)
  map_public_ip_on_launch = true
  tags = {
    Name = "public-subnet-${count.index}"
  }
}

resource "aws_subnet" "private" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 3)
  availability_zone       = element(["us-east-1a", "us-east-1b", "us-east-1c"], count.index)
  tags = {
    Name = "private-subnet-${count.index}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table_association" "public_subnet" {
  for_each      = { for idx, subnet in aws_subnet.public : idx => subnet.id }
  subnet_id     = each.value
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ecs_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ecs-security-group"
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs_task_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
      },
    ]
  })

  tags = {
    Name = "ecs-task-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "ecs-task-execution-role"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action    : "sts:AssumeRole",
        Effect    : "Allow",
        Principal : {
          Service : "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "ECS Task Execution Role"
  }
}


resource "aws_iam_policy" "ecs_s3_access" {
  name        = "ecs-s3-access-policy"
  description = "Policy for ECS tasks to access S3 bucket"

  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action   : [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Effect   : "Allow",
        Resource : [
          "arn:aws:s3:::my-s3-test-bucket02678",        # Replace with your S3 bucket ARN
          "arn:aws:s3:::my-s3-test-bucket02678/*"      # Replace with your S3 bucket objects ARN
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_custom_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ecs_s3_access.arn
}

resource "aws_ecs_cluster" "main" {
  name = "my-ecs-cluster"

  tags = {
    Name = "my-ecs-cluster"
  }
}
resource "aws_cloudwatch_log_group" "django-log-group" {
  name              = "/ecs/django-app"
  retention_in_days = 30
}
resource "aws_ecs_task_definition" "web_app" {
  family                   = "web-app-task"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256" # Adjust based on your application needs
  memory                   = "512" # Adjust based on your application needs

  container_definitions = jsonencode([
    {
      name      = "web-app"
      image     = "847712991543.dkr.ecr.us-east-1.amazonaws.com/image-editing-webapp:latest"
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        },
      ]
      logConfiguration={
        logDriver="awslogs"
        options = {
          awslogs-group= "/ecs/django-app",
        awslogs-region= "us-east-1",
        awslogs-stream-prefix= "django-app-log-stream"
        }
      }
    },
  ])

  tags = {
    Name = "web-app-task"
  }
}

resource "aws_ecs_service" "web_app" {
  name            = "web-app-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web_app.arn
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [for subnet in aws_subnet.public[*] : subnet.id]
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  desired_count = 1

  tags = {
    Name = "web-app-service"
  }
}



