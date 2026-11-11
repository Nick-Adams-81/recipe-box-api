## 2026-11-11 – Open API baseline

- Anonymous `GET /recipes` returns all recipes with `200 OK`.
- Anonymous `POST /recipes` with valid fields creates a new recipe and returns it with `201 Created`.
- Anonymous `DELETE /recipes/4` removes the recipe and returns `204 No Content`.