# Real Estate Attribute Package v1

**Status:** LOCKED
**Module:** Real Estate (Global, Residential, Commercial)

## 1. Summary
This document consolidates all attributes defined for the Real Estate module. It serves as the master reference for Backend validation, Frontend form generation, and Filter UI rendering.

| Key | Scope | Type | Filter Type | Mandatory? |
| :--- | :--- | :--- | :--- | :--- |
| `m2_gross` | Global | Number | Range (Min-Max) | Yes |
| `m2_net` | Global | Number | Range (Min-Max) | Yes |
| `building_status` | Global | Select | Multi-Select | No |
| `heating_type` | Global | Select | Multi-Select | No |
| `eligible_for_bank`| Global | Boolean | Checkbox (True only) | No |
| `swap_available` | Global | Boolean | Checkbox (True only) | No |
| `dues` | Global | Number | Range | No |
| `room_count` | Residential | Select | Multi-Select | **Yes** |
| `floor_location` | Residential | Select | Multi-Select | No |
| `bathroom_count` | Residential | Select | Select | No |
| `balcony` | Residential | Boolean | Checkbox | No |
| `furnished` | Residential | Boolean | Checkbox | No |
| `in_complex` | Residential | Boolean | Checkbox | No |
| `is_transfer` | Commercial | Boolean | Checkbox (True only) | No |
| `ceiling_height` | Commercial | Number | Range | No |
| `entrance_height` | Commercial | Number | Range | No |
| `power_capacity` | Commercial | Number | Range | No |
| `crane` | Commercial | Boolean | Checkbox | No |
| `ground_survey` | Commercial | Select | Select | No |
