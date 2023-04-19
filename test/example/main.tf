resource "aws_security_group" "sql_security_group" {
  description = "Security group for SQL Servers running on EC2"
  vpc_id      = 122433840
  tags        = ["app", "database"]
  name_prefix = var.prefix
}

locals {
  some_string = "22"
  ports        = [22, 3389]
}