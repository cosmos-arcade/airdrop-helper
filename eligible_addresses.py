import bech32
import json
from functions.helpers import convert_to_micro

# Load configuration file with env variables
with open('config.json', 'r') as f:
    config = json.load(f)

SNAPSHOTS = config['SNAPSHOTS']
DENIED_LIST = config['DENIED_LIST']
MINIMUM_AMOUNT = config['MINIMUM_AMOUNT']

# Addresses eligible for the airdrop
eligible_addresses: list = []

removed_addresses: dict = {}

print('\nStart processing ...\n\n')
# Iterate over snapshots
for snapshot in SNAPSHOTS:

    # Get chain name from snapshot name
    chain = snapshot.split('.')[1].split('_')[-1]

    print(f'Analyzing staking for {chain}\n')

    # Read snapshot's json file
    with open(snapshot, 'r') as f:
        snapshot_data = json.load(f)

    print(f'Number of delegations: {len(snapshot_data)}\n\n')
    # Iterate through all delegations
    for delegation in snapshot_data:
        delegator, amount, validator = delegation.values()
        
        # Skip SC addresses
        if len(delegator) > 43:
            continue

        # Skip if blacklisted delegator or validator
        if (delegator in DENIED_LIST) or (validator in DENIED_LIST):
            continue

        # Skip if required amount not met
        amount = float(amount)
        if amount < convert_to_micro(MINIMUM_AMOUNT[chain]):
            if delegator not in removed_addresses.keys():
                removed_addresses[delegator] = amount
                continue
            else:
                amount += removed_addresses[delegator]
                if amount < convert_to_micro(MINIMUM_AMOUNT[chain]):
                    removed_addresses[delegator] = amount
                    continue
    
        # Convert bech32 address to Juno chain
        if not delegator.startswith('juno'):
            decoded_address = bech32.bech32_decode(delegator)
            delegator = bech32.bech32_encode('juno', decoded_address[1])

        eligible_addresses.append(delegator)


eligible_addresses_no_duplicate = list(set(eligible_addresses))

print(f'Eligible adresses: {len(eligible_addresses_no_duplicate)}\n')

with open('./output/eligible_addresses.json', 'w') as outfile:
    json.dump(
        {'addresses': eligible_addresses_no_duplicate},
        outfile,
        indent=4
    )

