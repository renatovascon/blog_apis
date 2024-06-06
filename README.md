# blog-apis

## Setup

```bash
# subir aplicação
$ uvicorn app.main:app --reload

# para o ambiente de dev deve-se subir o proxy da aplicação
$ ./cloud-sql-proxy --address 0.0.0.0 --port 1234 tokwsv3:southamerica-east1:tokapi
```
