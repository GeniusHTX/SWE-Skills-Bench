# Task: Implement Smart Coupon Calculator

## Required File Paths (Agent must only modify/create under these)

- MUST modify: `src/calculator.py` — implement or update `SmartCouponCalculator` here.


## Background

We need a flexible discount calculation system for our e-commerce platform that can handle multiple promotion strategies simultaneously.

## Objective

Implement a `SmartCouponCalculator` class in `src/calculator.py` that supports the following discount strategies:

### Discount Rules

1. **Progressive Discount**
   - $10 off when order total ≥ $100
   - Additional $15 off (total $25 off) when order total ≥ $200

2. **Category Discount**
   - 10% off for items in specified promotional categories

3. **User Tier Discount**
   - VIP members: 5% off final price
   - SVIP members: 10% off final price

When multiple discounts apply, they should be stacked optimally to maximize customer savings.

## Implementation Requirements

### Core Functionality
- Calculate final price with all applicable discounts
- Support user tier levels: regular, VIP, SVIP
- Handle category-specific discounts
- Apply progressive discounts based on order total
- Implement optimal discount stacking logic

### Edge Cases to Handle
- Zero or negative amounts
- Empty shopping carts
- Invalid user tier values
- Items without category information

## Acceptance Criteria

- Calculator correctly applies all three discount types
- Discount stacking produces accurate final prices for complex scenarios
- Edge cases are handled gracefully without errors
- Code is maintainable and follows Python best practices
