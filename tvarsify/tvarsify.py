import argparse
import os
import logging
import sys

OPEN_BRACKET = "{"
CLOSED_BRACKET = "}"
SINGLE_QUOTE = "'"
DOUBLE_QUOTE = "\""
WHITESPACE = " "
COMMENT = "#"
EQUALS = "="
NEWLINE = "\n"
NAMESPACE_SEPERATOR = "_"
OPEN_LIST = "["
CLOSE_LIST = "]"
NOT_IMPLEMENTED = "Not yet implemented"


class TerraformModularize(object):
    variables: dict
    output_file: str
    input_loc: str

    def __init__(self, input_loc="../test/example/main.tf", output_file=None,
                 auto_vars_file="default.auto.tfvars", vars_file="variables.tf",
                 loglevel=logging.INFO, sort=True):
        logging.basicConfig(level=loglevel)
        self.input_loc = input_loc
        self.variables = {}
        self.auto_vars_file = auto_vars_file
        self.sort = sort
        if output_file is None:
            self.output_file = input_loc
        else:
            self.output_file = output_file
        self.vars_file = vars_file
        self.parsed_data = self.__parse_terraform()
        self.auto_tfvars_content = self.__gen_auto_tfvars()
        self.var_file_content = self.__gen_vars_file()

    def get_parsed_data(self):
        return self.parsed_data

    def write_parsed_data(self, path=None):
        if path is None:
            path = self.output_file
        with open(path, "w") as f:
            f.write(self.parsed_data)

    def __gen_auto_tfvars(self):
        auto_tfvars_content = ""
        pad_length = 0
        for k in self.variables.keys():
            pad_length = max(pad_length, len(k))

        if self.sort:
            for k in sorted(self.variables.keys()):
                auto_tfvars_content += k.ljust(pad_length) + " = " + self.variables[k]['value'] + "\n"
            return auto_tfvars_content
        # Unsorted
        for k, v in self.variables.items():
            auto_tfvars_content += k.ljust(pad_length) + " = " + v['value'] + "\n"
        return auto_tfvars_content

    def write_auto_tfvars(self, path=None):
        if path is None:
            path = self.auto_vars_file
        with open(path, "a+") as f:
            f.seek(0)
            current_vars = f.readlines()
            auto_vars_found = []
            if current_vars:
                if not current_vars[-1].endswith("\n"):
                    f.write("\n")
                for line in current_vars:
                    if line.strip().startswith(COMMENT):
                        continue
                    if "=" not in line:
                        continue
                    auto_vars_found.append(line.split("=", 1)[1].strip())
            for auto_var in self.auto_tfvars_content.split("\n"):
                if "=" not in auto_var:
                    if auto_var not in ["", "\n"]:
                        f.write(auto_var + "\n")
                elif auto_var.split("=", 1)[1].strip() not in auto_vars_found:
                    f.write(auto_var + "\n")

    def get_auto_tfvars(self):
        return self.auto_tfvars_content

    def __gen_vars_file(self):
        var_file_content = ""

        if self.sort:
            for k in sorted(self.variables.keys()):
                var_file_content += (self.generate_variable(k, self.variables[k]))
            return var_file_content.strip()
        # Unsorted
        for k, v in self.variables.items():
            var_file_content += (self.generate_variable(k, v))
        return var_file_content.strip()

    def write_vars_file(self, path=None):
        if path is None:
            path = self.vars_file
        with open(path, "a+") as f:
            f.seek(0)
            current_vars = f.readlines()
            vars_found = []
            if current_vars:
                if "".join(current_vars).endswith("\n\n"):
                    pass
                elif "".join(current_vars).endswith("\n"):
                    f.write("\n")
                else:
                    f.write("\n\n")

                for line in current_vars:
                    if line.startswith("variable"):
                        try:
                            start = line.index(SINGLE_QUOTE)
                            end = line[start + 1:].index(SINGLE_QUOTE)
                            vars_found.append(line[start + 1:start + end + 1])
                        except ValueError:
                            start = line.index(DOUBLE_QUOTE)
                            end = line[start + 1:].index(DOUBLE_QUOTE)
                            vars_found.append(line[start + 1:start + end + 1])
            skip = False
            for line in self.var_file_content.split("\n"):
                if line.startswith("variable"):
                    try:
                        variable_name = "".join(line[:line.index("{")].split('variable')[1:]).strip()[1:-1]
                        if variable_name in vars_found:
                            logging.info(f"{variable_name} already exists in variable file")
                            skip = True
                        else:
                            skip = False
                    except Exception:
                        logging.error(line)

                if skip:
                    continue
                f.write(line + "\n")

    def get_vars_file(self):
        return self.var_file_content

    def __parse_terraform(self):
        """
        Takes as input a directory OR file path
        Finds all the .tf files in the directory
        Parses the Terraform and build a dictionary
        :return:
        :rtype:
        """
        with open(self.input_loc, "r+") as f:
            data = f.read()
        data = data.strip()
        idx = self.get_next_bracket(data, 0)
        if idx == -1:
            return
        resource_namespace = self.get_resource_namespace(data[:idx])
        while idx != -1:
            data, idx = self.parse_key_values(data, idx, resource_namespace)
            idx = self.get_next_bracket(data, idx, CLOSED_BRACKET)
            idx = self.get_next_bracket(data, idx, OPEN_BRACKET)
            resource_namespace = self.get_resource_namespace(data[:idx])

        return data

    @staticmethod
    def generate_variable(k, v):
        return f'''
variable "{k}" {{
  type    = {v['type']}
  default = {v['value']}
}}
'''

    @staticmethod
    def get_resource_namespace(data):
        reverse = data[::-1]
        for idx, c in enumerate(reverse):
            if c == DOUBLE_QUOTE:
                start = idx
                end = reverse[start + 1:].index(DOUBLE_QUOTE)
                return reverse[start + 1:start + end + 1][::-1]
            elif c.isalnum():
                start = idx
                while reverse[idx].isalnum():
                    idx += 1
                return reverse[start:idx][::-1]

    @staticmethod
    def get_next_bracket(data, idx, bracket_type=OPEN_BRACKET):
        try:
            idx = idx + data[idx:].index(bracket_type)
        except ValueError as ve:
            idx = -1
        finally:
            return idx

    @staticmethod
    def out_of_bounds(data, idx):
        if idx + 1 >= len(data):
            logging.error("Invalid Terraform")
            sys.exit(1)

    def parse_key_values(self, data, idx, resource_namespace):
        idx = self.increment_and_lstrip(idx, data)
        end = self.get_end_key(data, idx)
        key = data[idx:idx + end]
        idx += end
        logging.debug(f"Found key: {key}")
        idx = self.increment_and_lstrip(idx, data)
        # Find the equals symbol
        end = data[idx:].index(EQUALS)
        idx += end

        # Parse the value
        idx = self.increment_and_lstrip(idx, data)
        end, data_type = self.get_end_value(data, idx)
        value = data[idx:idx + end]

        data, idx, skip = self.replace_var_with_data(data, idx, idx + end, key, resource_namespace, value)
        # idx += end
        logging.debug(f"Found value: {value}")
        if not skip:
            self.variables[f"{resource_namespace}{NAMESPACE_SEPERATOR}{key}"] = {"value": value, "type": data_type}
        # idx = increment_and_lstrip(idx, data, no_final_inc=True)
        if data[idx + 1:].lstrip()[0] != CLOSED_BRACKET:
            return self.parse_key_values(data, idx, resource_namespace)
        return data, idx

    @staticmethod
    def replace_var_with_data(data, start, end, key, resource_namespace, value):
        if value[0].isalpha() or value[0] == "$":
            return data, end, True
        replacement = f"var.{resource_namespace}{NAMESPACE_SEPERATOR}{key}"
        data = data[:start] + replacement + data[end:]
        return data, start + len(replacement), False

    @staticmethod
    def get_end_key(data, idx):
        start = data[idx:][0]
        if start == SINGLE_QUOTE:
            end = data[idx:].index(SINGLE_QUOTE)
        elif start == DOUBLE_QUOTE:
            end = data[idx:].index(DOUBLE_QUOTE)
        elif start == OPEN_BRACKET:
            # Skip to next line
            logging.error(NOT_IMPLEMENTED)
            sys.exit(1)
        elif start == COMMENT:
            # Skip to next line
            logging.error(NOT_IMPLEMENTED)
            sys.exit(1)
        else:
            end = data[idx:].index(WHITESPACE)
        return end

    @staticmethod
    def get_end_value(data, idx):
        start = data[idx:][0]
        data_type = "string"
        if start == SINGLE_QUOTE:
            end = data[idx + 1:].index(SINGLE_QUOTE) + 2
        elif start == DOUBLE_QUOTE:
            end = data[idx + 1:].index(DOUBLE_QUOTE) + 2
        elif start == OPEN_BRACKET:
            # Skip to next line
            logging.error(NOT_IMPLEMENTED)
            sys.exit(1)
        elif start == COMMENT:
            # Skip to next line
            logging.error(NOT_IMPLEMENTED)
            sys.exit(1)
        elif start == OPEN_LIST:
            q = [OPEN_LIST]
            end = 0
            while q:
                idx += 1
                end += 1
                if data[idx] == OPEN_LIST:
                    q.append(OPEN_LIST)
                elif data[idx] == CLOSE_LIST:
                    q.pop()
            end += 1
            data_type = "list(string)"
        else:
            end = min(data[idx:].index(WHITESPACE), data[idx:].index(NEWLINE))
            if data[idx:end].isnumeric():
                data_type = "number"

        return end, data_type

    def increment_and_lstrip(self, idx, data):
        self.out_of_bounds(data, idx)
        idx += 1
        # Take any left padding off data
        block = data[idx:].lstrip()
        idx += len(data[idx:]) - len(block)
        self.out_of_bounds(data, idx)
        return idx


def modularize(data):
    plan = data.PLAN
    if not os.path.isabs(plan):
        plan = os.path.abspath(plan)
    if os.path.isfile(plan) and plan[-3:] != ".tf":
        logging.error("Invalid Path found")
        sys.exit(1)

    if os.path.isdir(plan):
        files = [f for f in os.listdir(plan) if os.path.isfile(f) and f[-3:] == ".tf"]
        if not files:
            logging.error(f"No Terraform Files found in directory:\n{plan}")
            sys.exit(0)
        for found_plan in files:
            tf_mod = TerraformModularize(input_loc=found_plan, sort=not data.no_sort)
            print(tf_mod.get_parsed_data())
    else:
        if data.var_file is False:
            # Should be current user directory not off PLAN!!
            data.var_file = os.path.join(os.path.abspath(os.curdir), "variables.tf")
        if data.tfvars_file is False:
            data.tfvars_file = os.path.join(os.path.abspath(os.curdir), "default.auto.tfvars")
        output_file = plan[:-3] + "_generated" + plan[-3:]
        tf_mod = TerraformModularize(input_loc=plan, vars_file=data.var_file, auto_vars_file=data.tfvars_file,
                                     output_file=output_file, sort=not data.no_sort)
        logging.debug(
            f"\nGENERATED FILES\nOutput: {tf_mod.output_file}\nVariables: {tf_mod.vars_file}\nTFVARS: "
            f"{tf_mod.auto_vars_file}")
        tf_mod.write_parsed_data()
        tf_mod.write_vars_file()
        tf_mod.write_auto_tfvars()


def tvarsify_cli():
    print('-' * 88)
    print("Terraform Modularize")
    print('-' * 88)

    parser = argparse.ArgumentParser()
    parser.set_defaults(func=modularize)

    parser.add_argument("PLAN", help="Path to terraform *.tf plan file. Can be single file or directory")
    parser.add_argument("-no-defaults", help="Don't set values captured as default values in '-var-file' path",
                        action='store_true', required=False, default=False)

    parser.add_argument("-tfvars", action='store_true', required=False, default=False,
                        help="Add extracted variable values to the auto-file location"
                             " this defaults to 'defaults.auto.tfvars'")
    parser.add_argument("-tfvars-file",
                        help="Path to generate the tfvars file if '-tfvars' flag set defaults to "
                             "'defaults.auto.tfvars'",
                        required=False, default=False)
    parser.add_argument("-var-file", help="Path to generate the terraform variables file defaults to 'variables.tf",
                        required=False, default=False)
    parser.add_argument("-no-sort", action='store_true', required=False, default=False,
                        help="Do not sort the generated variables and tfvars files")
    # args = parser.parse_args(["../test/example/main.tf"])
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    tvarsify_cli()
