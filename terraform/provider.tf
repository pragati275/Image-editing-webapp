terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.77.0"
    }
  }
}

terraform {
  backend "s3" {
    bucket         = "s3statebackend5609"
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "images-tfstate-locking"
    encrypt        = true
    profile        = "terraform"
  }
}

provider "aws" {
  region = "us-east-1" # Specify your AWS region here
}