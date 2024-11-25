from core.generator import PETestsYAMLGenerator
import argparse
import json
import sys


def main():

    parser = argparse.ArgumentParser(
        description="Generate YAML test cases for PolicyEngine"
    )
    parser.add_argument(
        "--household",
        type=str,
        help="Input JSON file containing household data",
        required=True
    )
    parser.add_argument(
        "--variables",
        type=str,
        help="Input JSON file containing variables output data",
        required=True
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output YAML file name",
        required=True
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Test case name",
        default=None
    )

    args = parser.parse_args()

    try:

        with open(args.household, 'r') as f:
            household_data = json.load(f)

        with open(args.variables, 'r') as f:
            variables = json.load(f)

        generator = PETestsYAMLGenerator()

        yaml_data = generator.generate_yaml(
            household_data=household_data,
            name=args.name,
            pe_outputs=variables
        )

        generator.save_yaml(yaml_data, args.output)
        print(f"Successfully generated YAML file: {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
