# Task: Implement Low Stock Alert Feature for Saleor

## Background
   Implement an inventory alert feature in Saleor that automatically triggers
   alerts when product variant stock falls below a specified threshold.

## Files to Create/Modify
   - saleor/warehouse/models.py (add field to Stock)
   - saleor/warehouse/signals.py (add post_save handler)
   - saleor/plugins/manager.py (add plugin hook)
   - saleor/warehouse/tests/test_low_stock.py (new)

## Requirements
   
   Stock Model Update:
   - Add low_stock_threshold field (IntegerField, default=10)
   
   Signal Handler:
   - Create post_save signal on Stock model
   - When stock < threshold, publish LOW_STOCK event
   - Call plugin_low_stock_alert hook in plugin manager
   
   Caching (High Concurrency):
   - Use Django cache (redis backend)
   - Cache key: variant alert trigger state
   - TTL: 300 seconds
   - Prevent duplicate alerts for same variant
   
   Plugin Hook:
   - Add plugin_low_stock_alert method to manager

### Expected Functionality

   - Threshold trigger fires alert
   - Cache hit skips duplicate push
   - Cache expiry re-triggers alert
   - Above threshold no alert

## Acceptance Criteria

   - No Django system check errors
   - Cache correctly prevents duplicate alerts
