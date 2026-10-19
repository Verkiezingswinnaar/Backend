# TODO

- Verify that the aggregate current and previous vote totals use the intended comparison values: current `this_election_with_partials` and previous `last_election_corrected`.
- Deprecate the internal `this_election` and `last_election` totals when the aggregate calculation is updated. Keep them in the jsonl, so that they can be easily used if the API doesn't work as expected on election night.
- Design a dedicated municipal-election UI, separate from the Tweede Kamer and provincial presentation.
