import sys
import os
from jinja2 import Template

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python apply.py input_file output_file")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = f.read()

    t = Template(data)
    with open(sys.argv[2], "w") as f:
        f.write(t.render(os.environ))
