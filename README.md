# Batch-data-ingestion-using-Python

In this project I performed batched data ingestion using iterators in python, I setup my destination database- postgres and a pgadmin on docker wrote my code on jupyter notebook and pulled data from from NYC TLC site into my destination database.

The second part of this project involves dockerizing the data ingestion script. I converted the jupyter notebook to a script, created a dockerfile, created an image using the dockerfile and ran the image by passing the necessary parameters.


## Tools
* Docker
* Postgtes
* Python



## Running Postgres with Docker

#### Pull postgres image
```bash
Docker pull postgres
```
#### Run postgres image with the required parameters
```bash
docker run -it \
  -e POSTGRES_USER=myusername \
  -e POSTGRES_PASSWORD=myusername \
  -e POSTGRES_DB=nameofdatabase \
  -v /data:/var/lib/postgresql/data (create a folder where postgres will synchronize the Postgres data with the local folder. This ensures that Postgres data will be safely present within the Home Directory even if the Docker Container is terminated.) \
  -p 5432:5432 (in my case is used 5431:5432 because postgres on my laptop already uses 5432 port) \
  --name pg-database (name of the container)
  postgres
```

Now we have our postgres running


## Running pgadmin on docker

#### Pull pgadmin image
```bash
Docker pull dpage/pgadmin4
```
#### Running pgadmin image with the required parameters
```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --name pgadmin \
  dpage/pgadmin4
```


We can use pgadmin or pgcli to access our Postgres.
To access our postgres using pgadmin we need to create a docker network, this enables Postgres to connect to pgadmin. 

We can create one by running:
```bash
docker network create pg-network
```
After this we run both pgadmin and postgres images with the network

## Running Postgres and pgAdmin together

Run Postgres (change the path)

```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v c:/Users/alexe/git/data-engineering-zoomcamp/week_1_basics_n_setup/2_docker_sql/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13
```

Run pgAdmin

```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin-2 \
  dpage/pgadmin4
```
Now we can access postgres using pgadmin via the web on port 8080

To access postgres using pgcli run this command:
```bash
Pgcli -h hostname -p port -u username -d database
```



## Data ingestion

#### download the csv into current working directory from this site
```bash
URL="https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2021-01.csv"
```


#### Ingest data from csv into postgres using jupyter notebook
* Read the already downloaded csv file
* Inspect the data
* Perform minor transformations such as changing the date column that was in text to time stamp
* Since it will be ingested into postgres, generate a postgres schema from that data 
* Because the data is very large ingest it in chunks into the database




