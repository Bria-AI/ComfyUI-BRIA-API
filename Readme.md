# BRIA ComfyUI API Nodes

## Overview
This repository contains custom nodes for ComfyUI that allow access to BRIA's API endpoints. You can find our API documentation [here](https://bria-ai-api-docs.redoc.ly/#operation//generation/bria-v2/text-to-image).

To use the nodes in the workflow, you need a valid BRIA API token. You can get one [here](https://bria.ai/api/) (with 1000 free calls)

You can load the different workflows, by importing the compatible workflow.json files in this [folder](workflows). 

You can also download the following image and import it to comfyui:

<img src="./images/eraser_workflow.png" alt="Original image" width="500"/>

An illustration of the workflow:

 <img src="./images/bria_api_nodes_workflow_diagram.jpg" alt="all workflows example" width="650"/>

## Available Nodes

### Eraser
The **Eraser** node allows users to remove specific objects or areas from an image by providing a mask.

This functionality is powered by BRIA's ControlNet inpainting, available on [this model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-Inpainting) on Hugging Face.

You can also try out BRIA's Eraser demo by visiting our Hugging Face space [here](https://huggingface.co/spaces/briaai/BRIA-Eraser-API).

### GenFill
The **GenFill** node allows users to add and modify objects or areas in an image by providing a mask and a prompt.

This functionality is powered by BRIA's ControlNet Generative Fill, available on [this model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-Generative-Fill) on Hugging Face.

You can also try out BRIA's Generative Fill demo by visiting our Hugging Face space [here](https://huggingface.co/spaces/briaai/BRIA-Generative-Fill-API).

## Installation
There are two methods to install the BRIA ComfyUI API nodes:

### Method 1: Using ComfyUI's Custom Node Manager
1. Open ComfyUI.
2. Navigate to the [**Custom Node Manager**](https://github.com/ltdrdata/ComfyUI-Manager).
3. Click on 'Install Missing Nodes' or search for BRIA API and install the node from the manager.

### Method 2: Git Clone
1. Navigate to the `custom_nodes` directory of your ComfyUI installation:
   ```bash
   cd path_to_comfyui/custom_nodes
   ```
2. Clone this repository:
   ```bash
   git clone https://github.com/your-repo-link/ComfyUI-BRIA-API.git
   ```

3. Restart ComfyUI and load the workflows.
