# BRIA ComfyUI API Nodes

<p align="center" style="background-color:black; padding:10px;">
  <img src="./images/Bria Logo.svg" alt="BRIA Logo" width="200"/>
</p>

This repository provides custom nodes for ComfyUI, enabling direct access to **BRIA's API endpoints** for image generation workflows. **API documentation** is available [**here**](https://bria-ai-api-docs.redoc.ly/#operation//generation/bria-v2/text-to-image). 

An API token is required to use the nodes in your workflows. Get started quickly here
<a href="https://bria.ai/api/" style="text-decoration:none; vertical-align:middle;">
  <img src="https://img.shields.io/badge/GET%20YOUR%20TOKEN-1000%20Free%20Calls-blue?style=flat-square" alt="Get Your Token" height="20">
</a>.

To load a workflow, import the compatible workflow.json files from this [folder](workflows).  


<!-- Placeholder image of cool workflows. -->


 <!-- <img src="./images/bria_api_nodes_workflow_diagram.png" alt="all workflows example" width="400"/> <img src="./images/bria_api_nodes_workflow_diagram_2.png" alt="all workflows example" width="400"/> -->

# Available Nodes

## Image Generation Nodes
These nodes create high-quality images from text or image prompts, generating photorealistic or artistic results with support for various aspect ratios. [[API docs](https://bria-ai-api-docs.redoc.ly/tag/Image-Generation)].

### **Text2Image Base Node**
This node generates images from text prompts, serving as the foundation for creating visuals based on descriptive input. [[🤗model card](https://huggingface.co/briaai/BRIA-2.3)]

### **Text2Image Fast Node**
This node generates images from text prompts, optimized for speed. It provides faster results while maintaining quality. [[🤗model card](https://huggingface.co/briaai/BRIA-2.3-FAST)]

### **Text2Image HD Node**
This node generates images from text prompts, optimized for high-resolution outputs. It produces detailed and sharp visuals. [[🤗model card](https://huggingface.co/briaai/BRIA-2.2-HD)]

## Tailored Generation Nodes
These nodes use pre-trained tailored models to generate images that faithfully reproduce specific visual IP elements or guidelines. [[API docs](https://bria-ai-api-docs.redoc.ly/tag/Tailored-Generation)].

### **Tailored Gen**
This node generates images using a trained tailored model, reproducing specific visual IP elements or guidelines. Use the Tailored Model Info node to load the model's default settings.

### **Tailored Model Info**
This node retrieves the default settings and prompt prefix of a trained tailored model, which can be used to configure the Tailored Gen node.

## Image Editing Nodes
These nodes modify specific parts of images, enabling adjustments, while maintaining the integrity of the rest of the image.[[API docs](https://bria-ai-api-docs.redoc.ly/tag/Image-Editing)]

### **RMBG (Remove Background)**
This node removes the background from an image, isolating the foreground subject. Powered by BRIA's RMBG 2.0 model. [[🤗model Card](https://huggingface.co/briaai/RMBG-2.0)] [[🤗HF demo](https://huggingface.co/spaces/briaai/BRIA-RMBG-2.0)]

### **Replace Background**
This node replaces the background of an image while preserving the subject. The new background can be guided either by a provided reference image or generated based on a prompt. [[🤗model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-BG-Gen)]

### **Expand Image**
This node expands the dimensions of an image, generating new content to fill the extended areas.

### **Eraser**
This node is used to remove specific objects or areas from an image by providing a mask. Powered by BRIA's ControlNet inpainting [[🤗model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-Inpainting)] [[🤗HF demo](https://huggingface.co/spaces/briaai/BRIA-Eraser-API)].

### **GenFill**
This node is used to generate objects by prompt in a specific region of an image. This functionality is powered by BRIA's ControlNet Generative Fill. [[🤗model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-Generative-Fill)] [[🤗HF demo](https://huggingface.co/spaces/briaai/BRIA-Generative-Fill-API)]

### **Erase Foreground**
This node removes the foreground from an image, isolating the background.

## Product Shot Generation Nodes
These nodes create high-quality product images for eCommerce workflows. [[API docs](https://bria-ai-api-docs.redoc.ly/tag/Product-Shots-Generation)]

### **ShotByText**
This node is used to modify the background in an image by providing a prompt, This functionality is powered by BRIA's ControlNet Background-Generation.[[🤗ContrlNet model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-BG-Gen)] [[🤗HF demo](https://huggingface.co/spaces/briaai/Product-Shot-Generation)].

### **ShotByImage**
This node is used to modify the background in an image by providing a reference image. This functionality is powered by BRIA's ControlNet Background-Generation and BRIA's Image-Prompt. [[🤗ContrlNet model card](https://huggingface.co/briaai/BRIA-2.3-ControlNet-Inpainting)] [[🤗IP-Adapter model card](https://huggingface.co/briaai/Image-Prompt)] [[🤗HF demo](https://huggingface.co/spaces/briaai/Product-Shot-Generation)].

# Installation
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

<!-- ### Campaign generation
Coming soon -->
