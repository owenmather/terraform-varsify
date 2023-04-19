# terraform-varsify
!!**This Project is a Work In Progress and not ready for use**!!

_Docs auto-generated_

Modularize a terraform deployment automatically

Extracts hardcoded values from terraform and creates variables and optionally tfvars for hardcoded values  

## Install

```
pipx install tfvarsify
# Or Install local
pipx install .
```

## Usage

```readme
terraform-varsify -h
Usage: terraform-varsify [options] [PLAN]

Options:
  -tfvars                 Add extracted variable values to the auto-file location this defaults
                          to "defaults.auto.tfvars" can be set with "-tfvars-file"
                     
  -no-defaults            Don't set values captured as default values in "-var-file" path
  
  -prefix=gen             Adds a prefix too all generated variable names
  
  -tfvars-file=path       Path to generate the tfvars file if "-tfvars" flag set
                          defaults to "defaults.auto.tfvars"
                          
  -var-file=path          Path to generate the terraform variables file
                          defaults to "variables.tf"
```

## Explanation

Takes an existing terraform file or folder and converts all hardcoded values to variables

For example running `tvarsify example.tf`

---
### Before
<!-- BEGIN_EXAMPLE_INPUT -->
```terraform
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
```
<!-- END_EXAMPLE_INPUT -->
---
### After
#example.tf
<!-- BEGIN_GENERATED_TF -->
```terraform
resource "aws_security_group" "sql_security_group" {
  description = var.sql_security_group_description
  vpc_id      = var.sql_security_group_vpc_id
  tags        = var.sql_security_group_tags
  name_prefix = var.prefix
}

locals {
  some_string = var.locals_some_string
  ports        = var.locals_ports
}
```

#variables.tf Created/Updated with defaults
<!-- BEGIN_GENERATED_VARIABLES -->
```terraform
variable "locals_ports" {
  type    = list(string)
  default = [22, 3389]
}

variable "locals_some_string" {
  type    = string
  default = "22"
}

variable "sql_security_group_description" {
  type    = string
  default = "Security group for SQL Servers running on EC2"
}

variable "sql_security_group_tags" {
  type    = list(string)
  default = ["app", "database"]
}

variable "sql_security_group_vpc_id" {
  type    = string
  default = 122433840
}
```

If `-tfvars` flag is set a tfvars file will also be created/updated in `defaults.auto.tfvars` or the location set by setting `-tfvars-file=path`*

E.g. `tvarsify example.tf -tfvars -tfvars-file=generated.tfvars`  

#generated.tfvars Additonaly Created/Updated with extracted values
<!-- BEGIN_GENERATED_AUTO_TFVARS -->
```terraform
locals_ports                   = [22, 3389]
locals_some_string             = "22"
sql_security_group_description = "Security group for SQL Servers running on EC2"
sql_security_group_tags        = ["app", "database"]
sql_security_group_vpc_id      = 122433840

```

> *Note   
> `*.auto.tfvars` Files are picked up automatically running terraform  
> `*.tfvars` Files are **not** picked up automatically running terraform and must be activated with `-var-file`   
