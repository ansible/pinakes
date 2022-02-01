import sys
import os
from jinja2 import Template

# Apply environment variables to a Jinga2 Template file
# Save the results into an output file specified by the caller
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python apply_env.py input_file output_file")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = f.read()

    t = Template(data)
    with open(sys.argv[2], "w") as f:
        f.write(t.render(os.environ))
