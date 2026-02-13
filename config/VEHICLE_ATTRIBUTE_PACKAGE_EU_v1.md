# Vehicle Attribute Package EU v1

**Status:** DB Contract

## 1. Global (Mandatory)
| Key | Type | Filter |
| :--- | :--- | :--- |
| `brand` | Select | Multi |
| `model` | Text | Text/Select |
| `year` | Number | Range |
| `km` | Number | Range |
| `condition` | Select | Multi |

## 2. Cars (EU Focus)
| Key | Type | EU Mandatory? |
| :--- | :--- | :--- |
| `fuel_type` | Select | Yes |
| `gear_type` | Select | Yes |
| `emission_class`| Select | **Yes** (Critical for DE) |
| `engine_power_kw`| Number | Yes |

## 3. Validation Rules
-   `year`: 1900 - Current+1
-   `km`: 0 - 1,000,000
-   `emission_class`: Mandatory if `country=DE` (Soft check in UI, hard check in future).
