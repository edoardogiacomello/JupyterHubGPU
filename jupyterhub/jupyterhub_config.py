import os

### HUB CONFIGURATION ###
# Tells the hub to listen on all IP since it's run in a docker container
c.JupyterHub.hub_ip = '0.0.0.0'
# Tells the users to connect back to the HUB ip
c.JupyterHub.hub_connect_ip = os.environ["HUB_IP"]
# Defines the admins
c.Authenticator.admin_users = {'jhadmin'}
# Enables JupyterLab by default
c.Spawner.default_url = '/lab'

### AUTH CONFIGURATION ###

# Tells the default authenticator to create new UNIX users (inside the docker) for managing user-passwords
c.LocalAuthenticator.create_system_users = True


### DOCKERSPAWNER CONFIGURATION ###
# Select the Docker Spawner
c.JupyterHub.spawner_class = "docker"
# Tells the user containers to join the same network as the hub
c.DockerSpawner.network_name = os.environ["DOCKER_NETWORK_NAME"]
# IMPORTANT: Tells the docker services to enable GPU on user containers
c.DockerSpawner.extra_host_config = {'runtime': 'nvidia'}
# Tells to clenup user containers when they are stopped
c.DockerSpawner.remove = True

#### DEFINE USER IMAGES ####
# Dictionary of images that are proposed to the user. Image names should have already been built on the host machine
c.DockerSpawner.allowed_images = {'Tensorflow Latest':'jupytergpu/tensorflow-notebook', 'SciPy Only': 'jupytergpu/base-notebook'}

### USER CONTAINER CONFIGURATION ###
notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/'
# Setup the notebook root folder for the user
c.DockerSpawner.notebook_dir = notebook_dir

### USER VOLUME CONFIGURATION ###
# Mount the hub volumes to the user container
mounted_user_workdir = os.path.join(notebook_dir, 'work')
c.DockerSpawner.volumes = {
          '/home/jh_users/{username}/': {'bind': mounted_user_workdir, 'mode': 'rw'},
          '/mnt/sda2/': {'bind': os.path.join(notebook_dir, 'SHARED'), 'mode': 'ro'}
}

# FIX PERMISSION ON MOUNTED FOLDER
c.DockerSpawner.post_start_cmd = f'fix-permissions {mounted_user_workdir}'

