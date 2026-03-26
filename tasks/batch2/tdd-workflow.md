# Task: Implement a Discount Calculator Using Test-Driven Development

## Background

The Python TDD starter repository (https://github.com/tdd-starters/python) provides a minimal project scaffold for practicing test-driven development. Using this scaffold, build a calculator class that computes order totals with support for multiple discount strategies including category-based discounts, volume-based progressive discounts, and customer tier pricing.

## Files to Create

- `src/calculator.py` — Calculator implementation with discount logic
- `tests/test_calculator.py` — Comprehensive test suite written before or alongside the implementation

## Requirements

### Calculator Class

- Accept a list of order items and compute the final total after applying applicable discounts
- Each item should have at minimum a price, quantity, and category
- Support a customer tier parameter that affects pricing

### Discount Strategies

- **Category discount**: Certain product categories receive a fixed percentage discount
- **Progressive discount**: Orders above configurable quantity thresholds receive increasing discounts
- **Tier discount**: Different customer tiers (e.g., regular, silver, gold) receive different discount rates
- Discounts should stack in a defined order with clear precedence rules

### Test Suite

- Cover: normal computation, each discount type in isolation, combined discount scenarios, edge cases (empty cart, zero quantity, negative price rejection), and boundary conditions at discount thresholds
- Each test should have a descriptive name explaining the scenario

## Expected Functionality

- Given a set of items and a customer tier, the calculator returns the correct discounted total
- Invalid inputs (negative prices, missing required fields) are rejected with appropriate errors
- The discount application order is deterministic and documented by the test suite

## Acceptance Criteria

- The calculator computes correct totals for normal carts and for each discount strategy applied in isolation.
- Category, progressive, and customer-tier discounts combine in a deterministic order defined by the implementation.
- Invalid inputs such as negative prices or malformed items are rejected clearly.
- Edge cases including empty carts, zero quantities, and threshold boundaries behave predictably.
- The accompanying tests document the expected behavior well enough to drive the implementation through a TDD workflow.
