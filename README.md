# Batch-data-ingestion-using-Python

In this project I performed batched data ingestion using iterators in python, I setup my destination database- postgres and a pgadmin on docker wrote my code on jupyter notebook and pulled data from from NYC TLC site into my destination database.

The second part of this project involves dockerizing the data ingestion script. I converted the jupyter notebook to a script, created a dockerfile, created an image using the dockerfile and ran the image by passing the necessary parameters.


## Tools
* Docker
* Postgtes
* Python



## Running Postgres with Docker

## Pull postgres image
```bash
Docker pull postgres
```
## Run postgres image with the required parameters
```bash
docker run -it \
  -e POSTGRES_USER=myusername \
  -e POSTGRES_PASSWORD=myusername \
  -e POSTGRES_DB=nameofdatabase \
  -v /data:/var/lib/postgresql/data (create a folder where postgres will synchronize the Postgres data with the local folder. This ensures that Postgres data will be safely present within the Home Directory even if the Docker Container is terminated.) \
  -p 5432:5432 (in my case is used 5431:5432 because postgres on my laptop already uses 5432 port) \
  --name pg-database (name of the container)
  --network=pg-network ( it is the network used to connect postgres to pgadmin) \
  postgres
```
