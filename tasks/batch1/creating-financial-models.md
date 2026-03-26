# Task: Create QuantLib Usage Examples with DCF Valuation

## Background
   Add practical examples to the
   QuantLib repository demonstrating discounted cash flow (DCF) valuation
   using QuantLib's existing API.

## Files to Create/Modify
   - Examples/DCFValuation/DCFDemo.cpp (main example)
   - Examples/DCFValuation/CMakeLists.txt (build config)
   - Examples/DCFValuation/README.md (documentation)

## Requirements
   
   DCF Valuation Demo (DCFDemo.cpp):
   - Using QuantLib's YieldTermStructure for discount rates
   - Creating cash flow schedules with QuantLib::Schedule
   - Present value calculation using QuantLib::CashFlows::npv
   - Terminal value modeling
   
   Components to Demonstrate:
   - FlatForward term structure setup
   - FixedRateCoupon for regular cash flows
   - Simple bond-like cash flow structure
   - Sensitivity analysis (parallel shift in rates)
   
   Example Output:
   - NPV of cash flow stream
   - Individual discounted cash flows
   - Duration and convexity metrics

4. Build Integration:
   - CMakeLists.txt links against QuantLib
   - Can be built standalone after QuantLib is installed
   - Cross-platform (Windows, Linux, macOS)

## Acceptance Criteria
   - Example compiles and links against installed QuantLib
   - Output shows correct NPV calculations
   - README explains financial concepts and code structure
