FROM jupyterhub/jupyterhub
RUN pip install dockerspawner oauthenticator notebook # notebook is needed for launching notebooks
# Add a default admin user
RUN useradd -rm -s /bin/bash -g root -G sudo -u 1001 -p "$(openssl passwd -1 changeme)" jhadmin
WORKDIR /srv/jupyterhub
CMD jupyterhub
