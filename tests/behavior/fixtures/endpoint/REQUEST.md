# Requested change

Add `POST /items`.

- Accept a JSON-like mapping with a non-empty string `name`.
- Return status 201 and `{"item": {"name": NAME}}` for valid input.
- Return status 400 and `{"error": "name is required"}` otherwise.
- Add focused tests for both paths.
