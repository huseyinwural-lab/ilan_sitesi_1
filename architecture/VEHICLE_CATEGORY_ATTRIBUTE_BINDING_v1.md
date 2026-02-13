# Vehicle Category Attribute Binding v1

**Logic:** Inheritance Tree

1.  **Level 1: Vehicle (Root)**
    -   `brand`, `model`, `year`, `km`, `condition`, `warranty`, `swap`.
2.  **Level 2: Cars**
    -   Inherits Level 1.
    -   Adds: `fuel`, `gear`, `body`, `power`, `cc`, `emission`, `features`...
3.  **Level 2: Motorcycles**
    -   Inherits Level 1.
    -   Adds: `moto_type`, `power`, `cc`, `abs`.
4.  **Level 2: Commercial Vehicles**
    -   Inherits Level 1.
    -   Adds: `comm_type`, `payload`, `box`.
