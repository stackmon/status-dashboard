# start by pulling the python image
FROM python:3.10-alpine

RUN apk add build-base python3-dev libpq-dev

#RUN apt update || true \
#  && apt-get install -y python3-dev libpq-dev \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt gunicorn>=20.1.0 psycopg2>2.9

# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner
CMD ["gunicorn", "-b",  "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "-w", "2", \
     "app:create_app()"]
