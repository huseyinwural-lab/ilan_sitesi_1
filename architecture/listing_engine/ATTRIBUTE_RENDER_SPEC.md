# Attribute Render Spec

## 1. Objective
To generate frontend forms dynamically based on database configuration.

## 2. JSON Schema Contract
Endpoint: `GET /api/v1/attributes/form-schema/{category_id}`

### Response Format
```json
[
  {
    "key": "km",
    "label": "Kilometer",
    "type": "number",
    "required": true,
    "unit": "km",
    "options": [] 
  },
  {
    "key": "fuel_type",
    "label": "Fuel",
    "type": "select",
    "required": true,
    "options": [
      {"label": "Diesel", "value": "diesel"},
      {"label": "Petrol", "value": "gasoline"}
    ]
  }
]
```

## 3. UI Component Mapping
| Backend Type | React Component |
| :--- | :--- |
| `text` | `<Input type="text" />` |
| `number` | `<Input type="number" />` |
| `select` | `<Select />` |
| `multi_select` | `<CheckboxGroup />` |
| `boolean` | `<Switch />` |
| `date` | `<DatePicker />` |
