# 🚀 Non-Containerized SWE-bench Evaluation Setup

This guide helps you set up SWE-bench evaluation on a non-containerized environment where Docker can build images properly.

## 🎯 Why This Approach?

The current containerized environment has limitations:
- `unshare: operation not permitted` errors
- Docker-in-Docker restrictions
- Insufficient privileges for image building

## 📋 Prerequisites

- A local machine (Windows, macOS, or Linux) OR
- A cloud instance (AWS EC2, GCP, Azure) OR  
- A VM with proper Docker support
- At least 8GB RAM and 100GB disk space

## 🛠️ Quick Setup

### Option 1: Automated Setup (Linux/Ubuntu)

1. **Download and run the setup script:**
```bash
# Copy the setup script to your local machine
chmod +x setup_non_containerized.sh
./setup_non_containerized.sh
```

2. **Logout and login again** (to apply docker group changes)

3. **Run the evaluation:**
```bash
./run_evaluation.sh
```

### Option 2: Manual Setup

#### Step 1: Install Docker
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker  # or logout/login

# Verify installation
docker --version
docker run hello-world
```

#### Step 2: Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv swebench-env
source swebench-env/bin/activate

# Install packages
pip install --upgrade pip
pip install swebench datasets inspect-ai openai
```

#### Step 3: Create Predictions File
Create a file called `predictions.jsonl` with your generated predictions:

```json
{"instance_id": "astropy__astropy-11693", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/wcs/wcsapi/fitswcs.py b/astropy/wcs/wcsapi/fitswcs.py\nindex 1234567..89abcde 100644\n--- a/astropy/wcs/wcsapi/fitswcs.py\n+++ b/astropy/wcs/wcsapi/fitswcs.py\n@@ -323,7 +323,7 @@ class FITSWCS(BaseLowLevelWCS):\n \n     def world_to_pixel_values(self, *world_arrays):\n         pixel = self.all_world2pix(*world_arrays, 0)\n-        return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)\n+        return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel, quiet=True)\n \n     def array_index_to_world_values(self, *index_arrays):\n         return self.pixel_to_world_values(*index_arrays)\n```"}
{"instance_id": "astropy__astropy-12057", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/nddata/uncertainty_helpers.py b/astropy/nddata/uncertainty_helpers.py\nnew file mode 100644\nindex 0000000..e69de29\n--- /dev/null\n+++ b/astropy/nddata/uncertainty_helpers.py\n@@ -0,0 +1,49 @@\n+from astropy.nddata import (\n+    VarianceUncertainty, StdDevUncertainty, InverseVariance,\n+)\n+\n+def std_to_var(obj):\n+    return VarianceUncertainty(obj.array ** 2, unit=obj.unit ** 2)\n+\n+def var_to_invvar(obj):\n+    return InverseVariance(obj.array ** -1, unit=obj.unit ** -1)\n+\n+def invvar_to_var(obj):\n+    return VarianceUncertainty(obj.array ** -1, unit=obj.unit ** -1)\n+\n+def var_to_std(obj):\n+    return StdDevUncertainty(obj.array ** 0.5, unit=obj.unit ** 0.5)\n+\n+FUNC_MAP = {\n+    (StdDevUncertainty, VarianceUncertainty): std_to_var,\n+    (StdDevUncertainty, InverseVariance): lambda x: var_to_invvar(\n+        std_to_var(x)\n+    ),\n+    (VarianceUncertainty, StdDevUncertainty): var_to_std,\n+    (VarianceUncertainty, InverseVariance): var_to_invvar,\n+    (InverseVariance, StdDevUncertainty): lambda x: var_to_std(\n+        invvar_to_var(x)\n+    ),\n+    (InverseVariance, VarianceUncertainty): invvar_to_var,\n+    (StdDevUncertainty, StdDevUncertainty): lambda x: x,\n+    (VarianceUncertainty, VarianceUncertainty): lambda x: x,\n+    (InverseVariance, InverseVariance): lambda x: x,\n+}\n+\n+def convert_uncertainties(obj, new_class):\n+    return FUNC_MAP[(type(obj), new_class)](obj)\ndiff --git a/astropy/nddata/__init__.py b/astropy/nddata/__init__.py\nindex 72d9e88..dd4b77d 100644\n--- a/astropy/nddata/__init__.py\n+++ b/astropy/nddata/__init__.py\n@@ -10,3 +10,4 @@ from .nduncertainty import *\n from .nddata import *\n from .ndddata import *\n from .flag_collection import *\n+from .uncertainty_helpers import *\n```\n"}
{"instance_id": "astropy__astropy-12318", "model_name_or_path": "openai/gpt-4o", "model_patch": "```diff\ndiff --git a/astropy/modeling/physics.py b/astropy/modeling/physics.py\nindex 1234567..89abcde 100644\n--- a/astropy/modeling/physics.py\n+++ b/astropy/modeling/physics.py\n@@ -357,6 +357,9 @@ class BlackBody(Fittable1DModel):\n         # Linear in all parameters, no analytic derivatives\n         return (3000 * u.K, np.pi)\n \n+    def __init__(self, temperature, scale=1.0, **kwargs):\n+        super().__init__(temperature=temperature, scale=scale, **kwargs)\n+        self.scale = self.scale * u.dimensionless_unscaled\n \n     @property\n     def bolometric_flux(self):\n```"}
```

#### Step 4: Run Evaluation
```bash
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
```

## ☁️ Cloud Setup Options

### AWS EC2
```bash
# Launch instance with Docker
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.large \
    --key-name your-key \
    --security-group-ids sg-xxxxxxxxx \
    --user-data '#!/bin/bash
apt update
apt install -y docker.io
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu'
```

### Google Cloud Platform
```bash
# Create instance with Docker
gcloud compute instances create swebench-eval \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-standard-4 \
    --boot-disk-size=100GB \
    --metadata startup-script='#!/bin/bash
apt update
apt install -y docker.io
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu'
```

## 📊 Understanding the Results

After evaluation completes, you'll find:

- **Results JSON**: `openai__gpt-4o.local_eval_run.json`
- **Logs**: `logs/run_evaluation/local_eval_run/`
- **Key Metrics**:
  - `total_instances`: Total instances in dataset
  - `submitted_instances`: Instances your model attempted
  - `completed_instances`: Instances that completed evaluation
  - `resolved_instances`: Instances where patch fixed the issue
  - `resolution_rate`: Percentage of successfully resolved instances

## 🔧 Troubleshooting

### Docker Permission Issues
```bash
# If you get permission denied errors:
sudo usermod -aG docker $USER
newgrp docker
# or logout/login
```

### Insufficient Disk Space
```bash
# Check disk usage
df -h

# Clean up Docker if needed
docker system prune -a
```

### Slow Evaluation
- Reduce `--max_workers` to 2 or 1
- Use `--cache_level base` to reduce storage
- Ensure adequate RAM (8GB+ recommended)

## 🎉 Expected Outcome

With this setup, you should be able to:
- ✅ Build Docker images successfully
- ✅ Run full SWE-bench evaluation
- ✅ Get detailed results and logs
- ✅ Calculate resolution rates for your model

The first run will take longer as it builds all required Docker images, but subsequent runs will be much faster thanks to caching.
