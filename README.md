# JupyterHubGPU
 A Dockerized JupyterHub instance with JupyterLab, Tensorflow and GPU support
 
 This readme covers the necessary steps to replicate the provided configuration and information on how to further customise the configuration when needed.
 
 THIS ENVIRONMENT IS NOT FOR PRODUCTION AS NO STRONG SECURITY MEASURES ARE IN PLACE - USE IT AT YOUR OWN RISK.
 
 ## Features
 - Multi-user JupyterLab interface with Tensorflow and GPU support
 - The hub is run in a docker container
 - Each user notebook (Lab) is spawned in a dedicated docker container
 - Shared folder (e.g. Users homes and Data folders) are mounted in the user dockers for data persistance
 
 ## Pre-Requisites
 These packages has to be installed in the host machine (Currently running Ubuntu 20.04 LTS) package versions indicates currently installed versions:
 - Nvidia Cuda drivers (Currently: nvidia-driver-470 installed by Ubuntu "Additional Drivers" app)
 - docker (20.10.7)
 - docker-compose (1.25.0)
 - nvidia-docker2 (2.6.0)
 
 ## Preliminary steps
 1. Create a new user (e.g. ``` jupyterhub ```) in the host machine for managing jupyterhub and hosting the configuration files for the hub
 2. Add your user to ```docker``` group to enable docker commands without ```sudo```
 3. Test that GPUs are working in nvidia-docker by running ```docker run --rm --gpus all nvidia/cuda:10.1-base nvidia-smi ```
 4. Configure necessary shared folder mounts on the host machine,  - e.g. `/home/jh_users/` for hosting the user home folders (we keep them separated from UNIX host users) and `/mnt/sdb2/` for the shared data (datasets, models, etc.).
 
 ## Configure the setup environment
 The environment is built as a docker-compose app. Here we show the steps for replicating the configuration.
 Clone is repo or create a folder that will contain the setup environment (e.g. `/home/jupyterhub/JupyterHubGPU/`, indicated as the root from now on)
 ### Configuring the Hub Image
 - `./jupyterhub/` contains hub configuration and image.
 - `./jupyterhub/Dockerfile` defines the hub image. There we create the default admin `jhadmin` with a deafault password. This user will be present only on the hub container and can add new users from the hub control panel. We also set the WORKDIR to be `/srv/jupyterhub` and the default command to be the `jupyterhub` command that runs the hub server.
 - `./jupyterhub/jupyterhub_config.py` describes the configuration of the jupyterhub server application. Details are provided in the following sections.
 
 Building of this image will be done by the docker-compose, so we don't need to build it manually now.
 
 ### Building base user images
 User docker images are based on the fork [docker-stacks](https://github.com/edoardogiacomello/docker-stacks "docker-stacks"), customized to work with tensorflow and GPU support. 
 
 The `tensorflow-notebook` depends on `scipy-notebook` -> `minimal-notebook` -> `base-notebook`, so we need to rebuild the tree to add GPU support.
 
1.  Pull the [docker-stacks](https://github.com/edoardogiacomello/docker-stacks "docker-stacks") inside `./docker-stacks`
2. We need to add Cuda support to the base image. Since all the notebook images are based on `base-notebook`, open `./docker-stacks/base-notebook/Dockerfile` and edit the `ROOT_CONTAINER` argument as `ARG ROOT_CONTAINER=nvidia/cuda:11.4.2-cudnn8-runtime-ubuntu20.04`. The cuda image has to match the ubuntu distribution of `base-notebook` (Ubuntu Focal at the time of writing) and the requirements of `tensorflow` and your GPU.
3. Change the owner from `jupyter` to `jupytergpu` in `scipy-notebook`, `minimal-notebook`, and `base-notebook` Dockerfiles to avoid naming collisions with the official images
4. Build the tree of images in order (It will take some time):
	- `cd ./docker-stacks/base-notebook/`
	- `docker build -t "jupytergpu/base-notebook" .`
	- `cd ../minimal-notebook/`
	- `docker build -t "jupytergpu/minimal-notebook" .`
	- `cd ../scipy-notebook/`
	- `docker build -t "jupytergpu/scipy-notebook" .`
	- `cd ../tensorflow-notebook/`
	- `docker build -t "jupytergpu/tensorflow-notebook" .`

### Configuring Docker Environment with Docker-Compose
We use docker-compose to setup docker and the networking between containers.

1. Create a `.env` file in the root folder, along with the `docker-stacks` and `jupyterhub` folders. Write the project name `COMPOSE_PROJECT_NAME=jupyterhub` in the file. This will define the name of the network used by the containers.
2. Create the file `./docker-compose.yml` that specifies the hub image, mounted volumes and environment variables that will be used in `jupyterhub_config.py`:
	- `runtime:nvidia` enables gpu support in docker
	- `build: ./jupyterhub` Path to build when launching the application
	- `image: jupytergpu/jupyterhub` Name of the application image after build
	 `ports`: Maps host ports to hub ports (default is 8000:8000)
	 `container_name`: Name of the hub container when running
	 `volumes`: Define where to mount the host folders inside the hub container.
	 	 - `./jupyterhub:/srv/jupyterhub` Mounts the folder containing the hub configuration to the server root folder inside the container
		  - `/var/run/docker.sock:/var/run/docker.sock` Enables calls to docker service from inside a container, needed to spawn user containers.
		  - Here you can define your custom volumes to be mounted to the hub container (and subsequently in the user containers via `jupyterhub_config.py`)
	-  `environment:`
		 - `DOCKER_JUPYTER_CONTAINER`: Name given to user containers
		 - `DOCKER_NETWORK_NAME: ${COMPOSE_PROJECT_NAME}_default` defines the current docker network name. Uses the variable defined in `.env`
		 - `HUB_IP: jupyterhub-container` provides the user containers the ip for the hub

### Configuring JupyterHub
Get back to the `jupyterhub/jupyterhub_config.py` file for the configuration. The file has been commented for an easier understanding on what to edit in case of need.

The basic authenticator uses UNIX users inside the docker container for managing the password authentication. Other authenticators are available, such as GitHub Auth, please refer to Jupyterhub Documentation for advanced configuration.

**WARNING: Since docker-compose re-creates the container every time the configuration (i.e. docker-compose.yml or the Hub Dockerfile) changes, the current user configuration may be lost when updating the hub. This affect only login credentials and not the user files, that are permanently stored on the host**

## Running the Hub
To run for the first time, move to the root folder and run:
	`docker-compose up -d`
The optional `-d` argument launches the hub as a service.
	When run for the first time, this command will build the jupyterhub image and run the server on `<host-ip>:8000` The default login is : jhadmin, the password is defined in `./jupyterhub/Dockerfile`. 
**WARNING**:  As soon as you run the container for the first time or after every configuration update, change the admin password to a secure one! To do so, run `docker exec -it jupyterhub-container /bin/bash` and then `passwd jhadmin` for selecting a new password.

The next times the container can be started/stopped using: `docker-compose start` and `docker-compose stop` (e.g. when updating `jupyterhub_config.py`).

To stop and remove the container use `docker-compose down`.

## Adding new Users
- Run `docker exec -it jupyterhub-container /bin/bash` on the host
- Run `adduser <username>`
- Run `passwd <username>` and set a password
- Open the web interface, login as an admin and in the Admin menu (top bar) add a new user `<username>`.

## Adding new custom Docker images
To add new images, for example for freezing specific tensorflow versions, simply copy the structure of `tensorflow-notebook` and edit the Dockerfile accordingly. Then, build the image as done in the previous section and add the image to the list in `jupyterhub_config.py`.

## User environment
The user is provided with an instance of JupyterLab, with the following folder structure:
- ./work: The workdir that has persistance enabled - it is saved on `/home/jh_users/{username}/` on the host machine.
- ./SHARED: The shared data folder mounted as READ-ONLY for safety - it is saved on `/mnt/sda2/` on the host machine.


## Troubleshooting
### A volume is mounted without permissions for the user
The base-notebook image offer a script that fixes user permissions for a folder. However, dockerspawner creates user volume on runtime by using the root user of the container hub. This means that the "work" folder for a new user is owned by root and not by the user itself. The current workaround for this is to launch the fix-permission script after each spawn, using the hab configuration file. For the script to succeed, it is necessary that default user for the notebook container is root (and not jovyer). If you're using a custom image, make sure to set the USER as root at the end of the file (The notebook is still launched from the jovyer user and has no root access). 

### A user is present on the control panel but cannot login
The container may have been re-created, losing the UNIX PAM for that user. See "Adding new Users" and set a new password for the user.

