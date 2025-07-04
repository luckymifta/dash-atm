# Main Branch Reversion Notice

## Reversion Details
- **Date:** July 3, 2025
- **Reverted To Commit:** c06fcd5 ("feat: implement event-based ATM availability chart for consistent x-axis granularity")
- **Reversion Reason:** Terminal cash information functionality had errors that needed to be resolved

## Changes Reverted
The following changes were reverted from the main branch:

1. Cash information integration (commits c53e9e3 through 7d55e81)
2. Continuous operation mode (commits 90db97d and f591cab)
3. Import fixes for the combined ATM retrieval script (commit 477f3b2)

## Affected Features
- Terminal cash information retrieval and storage
- Continuous operation mode for ATM monitoring
- Import fixes for threading and deque in combined_atm_retrieval_script.py

## Next Steps
1. Address the identified errors in the terminal cash information functionality
2. Create a new branch for the fixed implementation
3. Re-implement the necessary changes with proper error handling
4. Test thoroughly before merging into the main branch again

## Recovery Plan
If needed, the reverted changes can be found in the following branches:
- `bugfix/sigit-cash-information` (last commit: 477f3b2)
- `feature/continuous-operation` (last commit: f591cab)
- `feature/sigit-cash-information` (last commit: 7d55e81)

These branches contain the work that was reverted and can be used as reference for reimplementing the features.
