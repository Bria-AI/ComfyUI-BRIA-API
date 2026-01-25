import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
  name: "BriaMultiImageSelect",

  async nodeCreated(node) {
    if (node.comfyClass !== "BriaMultiImageSelect") return;

    const getWidget = (name) =>
      node.widgets?.find(w => w.name === name);

    const pathsWidget = getWidget("selected_paths");
    if (!pathsWidget) return;

    pathsWidget.hidden = true;
    pathsWidget.draw = () => {};
    pathsWidget.computeSize = () => [0, 0];

    const viewURLFromRel = (rel) => {
      const parts = (rel || "").split("/");
      const filename = parts.pop();
      const subfolder = parts.join("/");
      const params = new URLSearchParams({ filename, type: "input", subfolder });
      return api.apiURL(`/view?${params.toString()}`);
    };

    const loadImg = (url) =>
      new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => resolve(img);
        img.onerror = () => reject();
        img.src = url;
      });

    const refreshPreview = async () => {
      let raw = node.properties.selected_paths;
      if (!raw) raw = pathsWidget.value;
      
      let rels = [];
      try {
        rels = raw ? JSON.parse(raw) : [];
      } catch (e) {
        console.error("Failed to parse selected_paths:", e);
        node.imgs = null;
        node.imgError = "Invalid image data";
        node.setDirtyCanvas(true, true);
        return;
      }

      if (!rels.length) {
        node.imgs = null;
        node.imgError = "No images selected";
        node.setDirtyCanvas(true, true);
        return;
      }

      const imgs = [];
      await Promise.allSettled(
        rels.map(async (rel) => {
          try {
            const img = await loadImg(viewURLFromRel(rel));
            imgs.push(img);
          } catch (e) {
            console.warn(`Failed to load image: ${rel}`, e);
          }
        })
      );

      if (imgs.length) {
        node.imgs = imgs;
        node.imgError = null;
      } else {
        node.imgs = null;
        node.imgError = "Failed to load images";
      }
      node.setDirtyCanvas(true, true);
    };
    // Update node size to accommodate preview
    const originalComputeSize = node.computeSize;
    node.computeSize = function () {
      const size = originalComputeSize ? originalComputeSize.apply(this, arguments) : [200, 100];
      size[1] = Math.max(size[1], 200); // Ensure minimum height for preview
      return size;
    };

    const btn = node.addWidget("button", "Select Images", null, async () => {
      const input = document.createElement("input");
      input.type = "file";
      input.multiple = true;
      input.accept = "image/*";
      input.style.display = "none";
      document.body.appendChild(input);

      input.onchange = async () => {
        const files = Array.from(input.files || []);
        document.body.removeChild(input);
        if (!files.length) return;

        const rels = [];

        for (const f of files) {
          const form = new FormData();
          form.append("image", f, f.name);

          const resp = await api.fetchApi("/upload/image", {
            method: "POST",
            body: form,
          });
          if (!resp.ok) continue;

          const data = await resp.json();
          const rel = data.subfolder
            ? `${data.subfolder}/${data.name}`
            : data.name;
          rels.push(rel);
        }

        const json = JSON.stringify(rels);
        pathsWidget.value = json;
        node.properties.selected_paths = json;

        await refreshPreview();
      };

      input.click();
    });

    node.widgets.unshift(
      node.widgets.splice(node.widgets.indexOf(btn), 1)[0]
    );

    // Initialize properties if not present
    if (!node.properties) {
      node.properties = {};
    }

    await refreshPreview();

    setTimeout(async () => {
      await refreshPreview();
    }, 100);
  },
});
