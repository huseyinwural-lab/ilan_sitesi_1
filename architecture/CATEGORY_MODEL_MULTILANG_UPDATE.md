# Category Model Multilang Update

**Requirement:** Database must store localized names and slugs flat or nested to support high-performance reads.

## 1. Schema Updates
We migrate from a simple `name` string to a JSONB structure or separate columns. Given Postgres `JSONB` efficiency:

```python
class Category(Base):
    # ...
    # Store all translations in JSONB
    # {
    #   "tr": {"name": "Daire", "slug": "daire"},
    #   "de": {"name": "Wohnung", "slug": "wohnung"},
    #   "fr": {"name": "Appartement", "slug": "appartement"}
    # }
    translations: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Sorting logic
    sort_order: Mapped[int] # Used for Sections (Housing vs Commercial)
    
    # Differentiation
    category_type: Mapped[str] # 'residential', 'commercial', 'land', 'project'
```

## 2. Indexing
-   GIN Index on `translations` to allow searching by slug/name in any language.
-   `ix_category_type` for filtering residential vs commercial.

## 3. Sorting Logic (App Layer)
Since sorting is language-dependent, the API logic will be:
```python
def get_categories(lang="tr"):
    cats = db.query(Category).all()
    # Sort in Python
    return sorted(cats, key=lambda c: c.translations[lang]['name'])
```
