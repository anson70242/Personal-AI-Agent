## App Server Stack - DevLog (2025/10/28 - Day 1)

**Milestone:** Project initialized. Deployed the base infrastructure on AWS Lightsail and successfully launched the Nginx container via Docker.

### System Setup
* **Host:** AWS Lightsail (`app-server-1`)
* **OS:** Ubuntu 24.04 LTS
* **Tech Stack:** Docker + Docker Compose

### Progress
* **Service (`nginx`):** Nginx is now functioning. It's serving a static `index.html` test page, accessible from the public IP (Port 80).
* **Version Control:** Initialized the `app-server-stack` project and pushed it to a private GitHub repository.
* **Vim Setup:** Configured the `.vimrc` file to automatically handle different indentations:
    * `yaml` files: 2 spaces
    * `nginx` / `conf` files: 4 spaces
    * Default: 4 spaces
    ```sh
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