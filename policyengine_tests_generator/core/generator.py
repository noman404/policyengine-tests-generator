# policyengine_tests_generator/core/generator.py
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import os
import numpy as np


class NoAliasDumper(yaml.SafeDumper):

    def ignore_aliases(self, data):
        return True


class PETestsYAMLGenerator:

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.output_dir = Path(__file__).parent.parent / "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_household_type(self, household_data: Dict[str, Any]) -> str:

        people = household_data["people"]

        has_dependents = any(
            person.get("age", {}).get("2023", 18) < 18
            for person in people.values()
        )

        if len(people) == 1:
            return "single"
        elif len(people) == 2 and not has_dependents:
            return "joint"
        else:
            return "dependent"

    def _get_year(self, json) -> str:
        state_name_data = json.get("households", {}).get("your household", {}).get("state_name", {})
        year = 0

        if state_name_data:
            year, state = next(iter(state_name_data.items()))
            print(f"Year: {year}, State: {state}")

        return str(year)

    def generate_yaml(
            self,
            household_data: Dict[str, Any],
            name: Optional[str] = None,
            pe_outputs: Any = None
    ) -> Dict[str, Any]:

        year_str = self._get_year(household_data)

        state_name = household_data["households"]["your household"]["state_name"][year_str].lower()
        household_type = self.detect_household_type(household_data)

        old_to_new_ids = self._map_person_ids(household_data["people"])

        members = [old_to_new_ids[m] for m in household_data["tax_units"]["your tax unit"]["members"]]

        config = {
            "name": name or f"Tax unit for {household_type} household ({year_str})",
            "absolute_error_margin": 0.01,
            "period": year_str,
            "input": {
                "people": {},
                "tax_units": {
                    "tax_unit": {
                        "members": members,
                        "tax_unit_childcare_expenses": 0,
                        "premium_tax_credit": 0,
                        "local_income_tax": 0,
                        "state_sales_tax": 0
                    }
                },
                "spm_units": {
                    "spm_unit": {
                        "members": members,
                        "snap": 0,
                        "tanf": 0
                    }
                },
                "households": {
                    "household": {
                        "members": members,
                        "state_fips": self._get_state_fips(
                            household_data["households"]["your household"]["state_name"][year_str]
                        )
                    }
                }
            },
            "output": {}
        }

        for item in pe_outputs:
            config['output'][item['variable']] = item['value']

        for old_id, person_data in household_data["people"].items():
            new_id = old_to_new_ids[old_id]
            config["input"]["people"][new_id] = self._generate_person_data(person_data, year_str)

        if has_use_tax_units(state_name):
            use_tax = f"{state_name.lower()}_use_tax"
            config["input"]["tax_units"]["tax_unit"][use_tax] = 0

        return config

    def _map_person_ids(self, people_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            old_id: f"person{i + 1}"
            for i, old_id in enumerate(people_data.keys())
        }

    def _generate_person_data(self, person_data: Dict[str, Any], year: str) -> Dict[str, Any]:
        return {
            "age": person_data["age"].get(year, 0),
            "employment_income": person_data["employment_income"].get(year, 0),
            "ssi": 0,
            "state_supplement": 0,
            "wic": 0,
        }

    def _get_state_fips(self, state_name: str) -> int:

        state_fips = {
            # States
            "AL": 1,
            "AK": 2,
            "AZ": 4,
            "AR": 5,
            "CA": 6,
            "CO": 8,
            "CT": 9,
            "DE": 10,
            "FL": 12,
            "GA": 13,
            "HI": 15,
            "ID": 16,
            "IL": 17,
            "IN": 18,
            "IA": 19,
            "KS": 20,
            "KY": 21,
            "LA": 22,
            "ME": 23,
            "MD": 24,
            "MA": 25,
            "MI": 26,
            "MN": 27,
            "MS": 28,
            "MO": 29,
            "MT": 30,
            "NE": 31,
            "NV": 32,
            "NH": 33,
            "NJ": 34,
            "NM": 35,
            "NY": 36,
            "NC": 37,
            "ND": 38,
            "OH": 39,
            "OK": 40,
            "OR": 41,
            "PA": 42,
            "RI": 44,
            "SC": 45,
            "SD": 46,
            "TN": 47,
            "TX": 48,
            "UT": 49,
            "VT": 50,
            "VA": 51,
            "WA": 53,
            "WV": 54,
            "WI": 55,
            "WY": 56,
            "DC": 11,
            "AS": 60,
            "GU": 66,
            "MP": 69,
            "PR": 72,
            "VI": 78,
        }

        return state_fips.get(state_name, 0)

    def save_yaml(self, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                  filename: str,
                  output_dir: Optional[Union[str, Path]] = None) -> Path:

        if not filename.endswith(('.yaml', '.yml')):
            filename += '.yaml'

        save_dir = Path(output_dir) if output_dir else self.output_dir
        os.makedirs(save_dir, exist_ok=True)
        file_path = save_dir / filename

        class FlowStyleRepresenter(NoAliasDumper):
            def represent_sequence(self, tag, sequence, flow_style=None):
                if any(isinstance(item, str) and item.startswith('person') for item in sequence):
                    flow_style = True
                return super().represent_sequence(tag, sequence, flow_style)

        with open(file_path, 'w') as f:
            if isinstance(data, list):
                yaml.dump_all(
                    data,
                    f,
                    Dumper=FlowStyleRepresenter,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                    explicit_start=True
                )
            else:
                yaml.dump(
                    data,
                    f,
                    Dumper=FlowStyleRepresenter,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2
                )

        return file_path

    def _get_yaml(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Generate YAML string from the data with clean number formatting.
        """

        class CustomDumper(NoAliasDumper):
            def represent_sequence(self, tag, sequence, flow_style=None):
                if any(isinstance(item, str) and item.startswith('person') for item in sequence):
                    flow_style = True
                return super().represent_sequence(tag, sequence, flow_style)

            def represent_float(self, data):
                # Convert to regular float and represent directly
                return self.represent_scalar('tag:yaml.org,2002:float', str(float(data)), style=None)

            def represent_int(self, data):
                # Convert to regular int and represent directly
                return self.represent_scalar('tag:yaml.org,2002:int', str(int(data)), style=None)

        # Register representers
        CustomDumper.add_representer(float, CustomDumper.represent_float)
        CustomDumper.add_representer(np.float64, CustomDumper.represent_float)
        CustomDumper.add_representer(np.float32, CustomDumper.represent_float)
        CustomDumper.add_representer(np.int64, CustomDumper.represent_int)
        CustomDumper.add_representer(np.int32, CustomDumper.represent_int)

        def clean_data(obj):
            if isinstance(obj, (np.float32, np.float64, float)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, dict):
                return {k: clean_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_data(i) for i in obj]
            return obj

        # Clean the data
        processed_data = clean_data(data)

        if isinstance(processed_data, list):
            return yaml.dump_all(
                processed_data,
                Dumper=CustomDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
                explicit_start=True
            )
        else:
            return yaml.dump(
                processed_data,
                Dumper=CustomDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2
            )


def has_use_tax_units(state) -> bool:
    has_use_tax = ['pa', 'nc', 'ca', 'il', 'in', 'ok']
    return state in has_use_tax
