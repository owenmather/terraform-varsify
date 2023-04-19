from tvarsify import TerraformModularize

EXAMPLE_START_STRING = "<!-- BEGIN_EXAMPLE_INPUT -->"
GENERATED_TF_STRING = "<!-- BEGIN_GENERATED_TF -->"
GENERATED_AUTO_TFVARS = "<!-- BEGIN_GENERATED_AUTO_TFVARS -->"
GENERATED_VARIABLES = "<!-- BEGIN_GENERATED_VARIABLES -->"
EXAMPLE_FILE = '../test/example/main.tf'


def gen_docs():
    tf_mod = TerraformModularize(input_loc=EXAMPLE_FILE)
    with open('../template.md') as f:
        readme = f.readlines()

    with open(EXAMPLE_FILE) as f:
        example_input_content = f.read()

    find_and_replace(readme, EXAMPLE_START_STRING, example_input_content)
    find_and_replace(readme, GENERATED_TF_STRING, tf_mod.get_parsed_data())
    find_and_replace(readme, GENERATED_AUTO_TFVARS, tf_mod.get_auto_tfvars())
    find_and_replace(readme, GENERATED_VARIABLES, tf_mod.get_vars_file())

    with open("../readme.md", "w") as f:
        f.writelines(readme)


def find_and_replace(content, find_str, replace):
    for idx, line in enumerate(content):
        if find_str in line:
            line += f"```terraform\n{replace}\n```\n"
            content[idx] = line
            break


if __name__ == "__main__":
    gen_docs()
