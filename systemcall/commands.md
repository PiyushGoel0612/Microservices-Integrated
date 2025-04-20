Run & Test
Build Docker Image:

docker build -t os-concepts-api .
Run Container:

docker run -p 8000:8000 os-concepts-api
Test with curl:

curl -X POST http://localhost:8000/api/os-concept \
  -H "Content-Type: application/json" \
  -d '{"concept": "fork"}'