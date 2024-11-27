terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.77.0"
    }
  }
}

provider "aws" {
  region  = "us-east-1" # Specify your AWS region here
  profile = "terraform" # Optional: Use this if you have a specific profile
}