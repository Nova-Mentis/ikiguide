# Build and Run Notes

## Docker Build

### Ikiguide Backend

```plaintext
cd ikiguide-backend

docker build -t ghcr.io/nova-mentis/ikiguide/ikiguide-backend:latest -f Dockerfile .
```

### Ikiguide Frontend

```plaintext
cd ikiguide-frontend

docker build -t ghcr.io/nova-mentis/ikiguide/ikiguide-frontend:latest -f Dockerfile .
```

## Docker Compose Build

```plaintext
docker compose build
```

## Docker Compose Run

```plaintext
docker compose up
```

## Docker Compose Down

```plaintext
docker compose down
```

## Run Manually

```plaintext
cd ../ikiguide-backend
uvicorn app.main:app --reload
```

```plaintext
cd ../ikiguide-frontend
npm start
```

## Docker Push

### Login

```plaintext
echo <YOUR_GITHUB_PAT> | docker login ghcr.io -u Nova-Mentis --password-stdin
```

### Push frontend image

```plaintext
docker push ghcr.io/nova-mentis/ikiguide/ikiguide-frontend:latest
```

### Push backend image

```plaintext
docker push ghcr.io/nova-mentis/ikiguide/ikiguide-backend:latest
```