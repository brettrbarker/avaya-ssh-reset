# avaya-1100-ssh-reset
SSH to a phone and perform a factory reset.

## Summary
This python script will take a CSV input with IP addresses for Avaya 1100 series phones (ex. 1120 and 1140) and will then attempt to SSH to them and perform a FACTORY RESET on each one. Proceed with caution.


### Usage
```
python ssh-reset.py sample-csv.csv
```
or specifically calling python 3 if it is not the default.
```
python3 ssh-reset.py sample-csv.csv
```