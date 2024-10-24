import subprocess
import os
import logging
from zipfile import ZipFile
import bz2
import requests

from setuptools import find_packages, setup
from setuptools.command.install import install

# Setup logging
logging.basicConfig(level=logging.INFO)

extras_require = {
    # Tasks
    "rewardbench": ["accelerate>=0.30.1,<=0.34.2", "bitsandbytes>=0.39.0", "black", "datasets>=2.16.0,<=2.21.0",
                    "deepspeed", "einops", "flake8>=6.0", "fschat", "hf_transfer",
                    "isort>=5.12.0", "peft", "tabulate", "tokenizers", "wandb",
                    "tiktoken==0.6.0", "transformers==4.43.4", "trl>=0.8.2"], # For llama3
    
    # Metrics
    "gemba": ["openai>=1.0.0", "openai-clip", "termcolor", "pexpect", "ipdb",
               "absl-py", "six"],
    
    # Regressor
    "xgboost": ["xgboost>=2.1.1", "scikit-optimize"],
    
    # Misc
    "dev": ["pytest"],
}

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define the base class for extra installs
class CustomInstall(install):
    description = 'Run additional shell commands for setup'
    user_options = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    def run(self):
        # Run the standard installation process first
        install.run(self)
        
        os.system("git submodule update --init --recursive")
        os.system("git submodule update")
        
        # Run custom post-installation
        self.install_metric_bleurt()
        self.install_metric_rouge()
        self.install_metric_meteor()
        self.install_spacy()
        self.install_task_wmt()
    
    @staticmethod
    def install_metric_bleurt():   
        # Navigate to the bleurt directory
        bleurt_dir = os.path.join(CustomInstall.root_dir, 'src', 'metametrics', 'metrics', 'bleurt')
        os.chdir(bleurt_dir)

        # Install BLEURT
        logging.info("Installing BLEURT ...")
        subprocess.run(["pip", "install", "."], check=True)

        # Download BLEURT model if necessary
        bleurt_model_path = os.path.join(bleurt_dir, "BLEURT-20")
        if not os.path.exists(bleurt_model_path):
            bleurt_zip_path = os.path.join(bleurt_dir, "BLEURT-20.zip")
            logging.info("Downloading BLEURT-20 model...")
            with requests.get("https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip", stream=True) as r:
                with open(bleurt_zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            with ZipFile(bleurt_zip_path, 'r') as zip_ref:
                zip_ref.extractall(bleurt_dir)
            os.remove(bleurt_zip_path)
        logging.info("BLEURT installed successfully.")

    @staticmethod
    def install_metric_rouge():       
        # Setup for ROUGE
        metrics_dir = os.path.join(CustomInstall.root_dir, 'src', 'metametrics', 'metrics')
        os.chdir(metrics_dir)
        
        os.environ["ROUGE_HOME"] = os.path.join(metrics_dir, "ROUGE-1.5.5")
        os.environ["LC_ALL"] = "C.UTF-8"
        os.environ["LANG"] = "C.UTF-8"

        # Setup for ROUGE
        os.system("pip install git+https://github.com/bheinzerling/pyrouge.git")
        
        # Remove current ROUGE if exists and reinstall
        os.system("rm -rf ROUGE-1.5.5")
        subprocess.run(["curl", "-L", "https://github.com/Yale-LILY/SummEval/tarball/7e4330d", "-o", "project.tar.gz", "-s"])
        subprocess.run(["tar", "-xzf", "project.tar.gz"])
        subprocess.run(["mv", "Yale-LILY-SummEval-7e4330d/evaluation/summ_eval/ROUGE-1.5.5/", "ROUGE-1.5.5"])
        os.system("rm project.tar.gz")
        os.system("rm -rf Yale-LILY-SummEval-7e4330d/")
        logging.info("ROUGE setup completed.")
        
        # Download word embeddings for ROUGE-WE metric
        os.system("rm -rf embeddings")
        os.system("mkdir embeddings")
        embeddings_path = os.path.join(metrics_dir, "embeddings", "deps.words")
        if not os.path.exists(embeddings_path):
            logging.info("Downloading word embeddings")
            url = "https://u.cs.biu.ac.il/~yogo/data/syntemb/deps.words.bz2"
            r = requests.get(url)
            d = bz2.decompress(r.content)
            with open(embeddings_path, "wb") as outputf:
                outputf.write(d)
    
    @staticmethod
    def install_metric_meteor():
        # Setup for METEOR
        metrics_dir = os.path.join(CustomInstall.root_dir, 'src', 'metametrics', 'metrics')
        os.chdir(metrics_dir)
        meteor_url = 'https://github.com/Maluuba/nlg-eval/blob/master/nlgeval/pycocoevalcap/meteor/meteor-1.5.jar?raw=true'
        response = requests.get(meteor_url)
        with open(os.path.join(metrics_dir, "meteor-1.5.jar"), "wb") as f:
            f.write(response.content)
        logging.info("METEOR installed successfully.")
    
    @staticmethod
    def install_spacy():
        # Install spacy for SummaQA
        subprocess.run("pip install spacy", shell=True, check=True, text=True, capture_output=True)
    
    @staticmethod
    def install_task_wmt():
        # Navigate to the tasks/mteval
        os.chdir(os.path.join(CustomInstall.root_dir, 'src', 'metametrics', 'metametrics_tasks'))
        os.system("rm -rf mt-metrics-eval")
        if not os.path.isdir('mt-metrics-eval'):
            logging.info("Cloning mt-metrics-eval ...")
            subprocess.run(["git", "clone", "https://github.com/google-research/mt-metrics-eval.git"])
        os.chdir("mt-metrics-eval")
        logging.info("Installing mt-metrics-eval ...")
        subprocess.run(["pip", "install", "."], check=True)

setup(
    name="metametrics",
    version="0.0.1",
    author="Genta Indra Winata",
    author_email="gentaindrawinata@gmail.com",
    description="MetaMetrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0 License",
    url="https://github.com/meta-metrics/meta-metrics",
    project_urls={
        "Bug Tracker": "https://github.com/meta-metrics/meta-metrics/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=[
        "transformers>=4.41.2,<=4.45.2",
        "torch>=2.0.1",
        "tensorflow",
        "tf-slim>=1.1",
        "torchvision",
        "unbabel-comet==2.2.2",
        "requests",
        "pandas>=2.0.0",
        "numpy>=1.26.3",
        "scipy",
        "scikit-learn",
        "sacrebleu>=2.4.2",
        "bayesian-optimization",
        "evaluate>=0.4.2",
        "sentencepiece",
        "nltk>=3.8.1",
        "dill==0.3.1.1", # for apache-beam
        "regex",
        "gdown",
        "tqdm"
    ],
    package_dir={"": "src"},
    packages = find_packages("src"),
    extras_require=extras_require,
    python_requires=">=3.10",
    cmdclass={
        'install': CustomInstall,
    },
)
