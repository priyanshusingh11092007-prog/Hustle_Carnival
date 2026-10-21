# Queue Rules

## Token Order

Tokens are assigned in increasing order within each service.

## Waiting

New tokens begin in WAITING status.

## Calling

Only WAITING tokens can be called.

Only one CALLED or SERVING token is permitted per service
by the application workflow.

## Serving

CALLED tokens become SERVING when service begins.

## Completion

Only SERVING tokens can be completed.

## Hold

SERVING tokens can be placed on HOLD.

Held tokens can return to WAITING.

## Cancellation

WAITING and CALLED tokens can be cancelled.

Customers can cancel their own WAITING token using its private link.

## No-show

Only CALLED tokens can become NO_SHOW.

## Walk-ins

Walk-ins join the same digital queue.

## Notes

A real deployment must establish a no-show grace period,
priority policies, staff permissions, opening hours and
manual fallback procedures.
