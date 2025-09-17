#!/bin/bash
# Setup script for non-containerized SWE-bench evaluation

echo "🚀 Setting up non-containerized SWE-bench evaluation environment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root"
    exit 1
fi

# Install Docker
echo "📦 Installing Docker..."
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER

# Install Python dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv swebench-env
source swebench-env/bin/activate
pip install --upgrade pip
pip install swebench datasets inspect-ai openai

# Create predictions file
echo "📝 Creating predictions file..."
cat > predictions.jsonl << 'EOF'
{"instance_id": "astropy__astropy-11693", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/wcs/wcsapi/fitswcs.py b/astropy/wcs/wcsapi/fitswcs.py\nindex 1234567..89abcde 100644\n--- a/astropy/wcs/wcsapi/fitswcs.py\n+++ b/astropy/wcs/wcsapi/fitswcs.py\n@@ -323,7 +323,7 @@ class FITSWCS(BaseLowLevelWCS):\n \n     def world_to_pixel_values(self, *world_arrays):\n         pixel = self.all_world2pix(*world_arrays, 0)\n-        return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)\n+        return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel, quiet=True)\n \n     def array_index_to_world_values(self, *index_arrays):\n         return self.pixel_to_world_values(*index_arrays)\n```"}
{"instance_id": "astropy__astropy-12057", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/nddata/uncertainty_helpers.py b/astropy/nddata/uncertainty_helpers.py\nnew file mode 100644\nindex 0000000..e69de29\n--- /dev/null\n+++ b/astropy/nddata/uncertainty_helpers.py\n@@ -0,0 +1,49 @@\n+from astropy.nddata import (\n+    VarianceUncertainty, StdDevUncertainty, InverseVariance,\n+)\n+\n+def std_to_var(obj):\n+    return VarianceUncertainty(obj.array ** 2, unit=obj.unit ** 2)\n+\n+def var_to_invvar(obj):\n+    return InverseVariance(obj.array ** -1, unit=obj.unit ** -1)\n+\n+def invvar_to_var(obj):\n+    return VarianceUncertainty(obj.array ** -1, unit=obj.unit ** -1)\n+\n+def var_to_std(obj):\n+    return StdDevUncertainty(obj.array ** 0.5, unit=obj.unit ** 0.5)\n+\n+FUNC_MAP = {\n+    (StdDevUncertainty, VarianceUncertainty): std_to_var,\n+    (StdDevUncertainty, InverseVariance): lambda x: var_to_invvar(\n+        std_to_var(x)\n+    ),\n+    (VarianceUncertainty, StdDevUncertainty): var_to_std,\n+    (VarianceUncertainty, InverseVariance): var_to_invvar,\n+    (InverseVariance, StdDevUncertainty): lambda x: var_to_std(\n+        invvar_to_var(x)\n+    ),\n+    (InverseVariance, VarianceUncertainty): invvar_to_var,\n+    (StdDevUncertainty, StdDevUncertainty): lambda x: x,\n+    (VarianceUncertainty, VarianceUncertainty): lambda x: x,\n+    (InverseVariance, InverseVariance): lambda x: x,\n+}\n+\n+def convert_uncertainties(obj, new_class):\n+    return FUNC_MAP[(type(obj), new_class)](obj)\ndiff --git a/astropy/nddata/__init__.py b/astropy/nddata/__init__.py\nindex 72d9e88..dd4b77d 100644\n--- a/astropy/nddata/__init__.py\n+++ b/astropy/nddata/__init__.py\n@@ -10,3 +10,4 @@ from .nduncertainty import *\n from .nddata import *\n from .ndddata import *\n from .flag_collection import *\n+from .uncertainty_helpers import *\n```\n"}
{"instance_id": "astropy__astropy-12318", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/modeling/physics.py b/astropy/modeling/physics.py\nindex 1234567..89abcde 100644\n--- a/astropy/modeling/physics.py\n+++ b/astropy/modeling/physics.py\n@@ -357,6 +357,9 @@ class BlackBody(Fittable1DModel):\n         # Linear in all parameters, no analytic derivatives\n         return (3000 * u.K, np.pi)\n \n+    def __init__(self, temperature, scale=1.0, **kwargs):\n+        super().__init__(temperature=temperature, scale=scale, **kwargs)\n+        self.scale = self.scale * u.dimensionless_unscaled\n \n     @property\n     def bolometric_flux(self):\n```"}
EOF

# Create evaluation script
echo "📜 Creating evaluation script..."
cat > run_evaluation.sh << 'EOF'
#!/bin/bash
echo "🚀 Running SWE-bench evaluation..."

# Activate virtual environment
source swebench-env/bin/activate

# Run evaluation
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench \
    --predictions_path predictions.jsonl \
    --max_workers 4 \
    --run_id local_eval_run \
    --cache_level env \
    --force_rebuild True \
    --namespace none

echo "✅ Evaluation completed! Check the results in the current directory."
EOF

chmod +x run_evaluation.sh

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Logout and login again (or run 'newgrp docker') to apply docker group changes"
echo "2. Verify Docker installation: docker run hello-world"
echo "3. Run the evaluation: ./run_evaluation.sh"
echo ""
echo "⚠️  Note: The first run will take longer as it builds Docker images"
echo "📊 Disk space: Make sure you have at least 100GB free space"
echo ""
