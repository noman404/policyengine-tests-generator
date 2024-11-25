A Python package for generating test cases for PolicyEngine simulations. This package helps create structured test configurations from different household types including single, joint, and households with dependents.


```bash
pip install -e .
```


To run it from cli
```bash
python policyengine-tests-generator\main.py --household input\input.json --variables input\output.json --output test.yaml
```

there will be an `output` dir with yaml test file in the `policyengine-tests-generator/output/`