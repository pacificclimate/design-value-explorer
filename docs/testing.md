# Testing

We use the `pytest` framework for unit tests, which are in director 
`tests/`.

Unit tests are automatically run by a GitHub actions workflow on commit 
pushes.

## Running tests

We primarily use a Docker image to run the code for testing and 
development. For details on running that image, see
[Deploying locally for development](deployment. md#deploying-locally-for-development).

To run tests, connect to a bash shell inside the container as instructed
in the "Deploying locally...", then issue the command:

```
pipenv run pytest -s -v /codebase/tests
```
