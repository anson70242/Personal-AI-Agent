# App Server Stack - DevLog
## 2025-10-29 - Day 2

**Today Goal:** Setup the vllm server, configure nginx to forward LLM api request to vllm server.

First, `ssh` to the GPU server.

- Docker Installation: 

  ```sh
  sudo apt install docker.io docker-compose -y
  ```

- Installing the NVIDIA Container Toolkit (With `apt`: Ubuntu, Debian) for vllm container [Source](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

  1. Install the prerequisites for the instructions below:

     ```sh
     sudo apt-get update && sudo apt-get install -y --no-install-recommends \
        curl \
        gnupg2
     ```

  2. Configure the production repository:

     ```sh
     curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
       && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
         sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
         sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
     ```

  3. Update the packages list from the repository:

     ```sh
     sudo apt-get update
     ```

  4. Install the NVIDIA Container Toolkit packages:
     ```sh
     export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.18.0-1
       sudo apt-get install -y \
           nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
           nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
           libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
           libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
     ```

- Configuration

  1. Configure the container runtime by using the `nvidia-ctk` command:

     ```sh
     sudo nvidia-ctk runtime configure --runtime=docker
     ```

     The `nvidia-ctk` command modifies the `/etc/docker/daemon.json` file on the host. The file is updated so that Docker can use the NVIDIA Container Runtime.

  2. Restart the Docker daemon:

     ```sh
     sudo systemctl restart docker
     ```


Second, deploy vllm container:

1. Export your huggingface token:
   ```sh
   export HF_TOKEN="#your hf token here"
   ```

2. Use vLLM's Official Docker Image

   ```sh
   docker run --runtime nvidia --gpus all \
       -v ~/.cache/huggingface:/root/.cache/huggingface \
       --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
       -p 8000:8000 \
       --ipc=host \
       vllm/vllm-openai:latest \
       --model Qwen/Qwen3-0.6B
   ```

## 2025-10-28 - Day 1

**Milestone:** Project initialized. Deployed the base infrastructure on AWS Lightsail and successfully launched the Nginx container via Docker.

### System Setup
* **Host:** AWS Lightsail (`app-server-1`)

* **OS:** Ubuntu 24.04 LTS

* **Tech Stack:** Docker + Docker Compose

  * Docker Installation: 

    ```sh
    sudo apt install docker.io docker-compose -y
    ```
  
  * Docker Compose file:
  
    ```yaml
    version: '3.8' # commendlly used version
    
    services:
      nginx:
        build: ./nginx # indicate the path to the Dockerfile
        ports:
          - 80:80 # map host port 80 to container port 80
        # restart when the container when it stops unexpectedly
        restart: unless-stopped 
    ```
  
    
  


### Progress
* **Service (`nginx`):** Nginx is now functioning. It's serving a static `index.html` test page, accessible from the public IP (Port 80).

    * For `nginx`, I created 3 file: 

        * Dockerfile, create the nginx continer.

            ```dockerfile
            # Use the official Nginx image as the base image
            FROM nginx:alpine
            # Remove the default Nginx configuration file
            RUN rm /etc/nginx/conf.d/default.conf
            # Copy the custom Nginx configuration file to the container
            COPY nginx.conf /etc/nginx/conf.d
            # Copy the static HTML file to the Nginx HTML directory
            COPY index.html /usr/share/nginx/html
            ```
        
        * nginx.conf, for custom configuraction.
        
            ```conf
            server {
                listen 80; # Listen on port 80
                location / {
                    # Serve static files from the specified directory
                    root /usr/share/nginx/html;
                    # Default file to serve
                    index index.html index.htm;
                }
            }
            ```
        
        * index.html, for a static html page, for testing.
        
            ```html
            <h1>Nginx is working!</h1>
            <p>This is the test page from your app-server-1.</p>
            ```
        
            

* **Version Control:** Initialized the `app-server-stack` project and pushed it to a private GitHub repository.

* **Vim Setup:** Configured the `.vimrc` file to automatically handle different indentations:
    * `yaml` files: 2 spaces
    * `nginx` / `conf` files: 4 spaces
    * Default: 4 spaces
    ```vimrc
    filetype plugin indent on
    
    set tabstop=4
    set shiftwidth=4
    set expandtab
    set number
    
    autocmd FileType yaml setlocal tabstop=2 shiftwidth=2 expandtab
    autocmd FileType conf setlocal tabstop=4 shiftwidth=4 expandtab
    autocmd FileType nginx setlocal tabstop=4 shiftwidth=4 expandtab
    ```

### Next Steps
* Begin building the `mcp_server` (FastAPI) service.