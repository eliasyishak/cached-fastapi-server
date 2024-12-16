### Purpose

I created this project to demonstrate how to setup a FastAPI application to act
as a caching server for the GitHub related queries. I took a containerized approach
to solving this problem by spinning up one (or more) FastAPI containers and one redis
container.

### Getting Started

To run this application, the recommended approach is to run it through Docker. The root
of this project contains a [docker-compose.yml](docker-compose.yml) file that spins up
the necessary containers.

To set the port you would like to access the application on, you can edit the docker-compose configuration file to map to a different port. Currently it is mapped to
port `8000` on the host machine so the root endpoint can be accessed at [http://localhost:8000](http://localhost:8000) once the application is running

```yaml
  server:
    container_name: server
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000" <-- change the first port
```

To run the application, you can simply run the command below from the root directory

```zsh
docker-compose up --build
```

Once the containers are running, we can use the docs page for the FastAPI server to see all
of our endpoints that have been defined. You can reach this page through your broswer by
going to [http://localhost:8000/docs](http://localhost:8000/docs) if you have not changed the default port. The page should look like the below screenshot.

![FastAPI docs page](assets/docs-screenshot.png)

### Environment Variables

The GitHub REST API is rate limited heavily if you don't provide a `GITHUB_API_TOKEN`. In order to ensure that we don't hit the most conservative rate limit, we should pass this API token. This can be done by setting the variable with the command above.

```zsh
GITHUB_API_TOKEN=YOUR_TOKEN_HERE docker-compose up --build
```

### Running Tests

Tests are provided for this project to test the functionality of our endpoints. This test
suite is defined in the [api-suite.sh](api-suite.sh) file.
