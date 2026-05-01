# Spec

## Invariants

- Anonymous users cannot view invoices.
- A signed-in user can view only their own invoice.
- Admin users can view any invoice.

## Acceptance Checks

- Non-owner access is rejected.
- Owner access is allowed.
- Admin access is allowed.
