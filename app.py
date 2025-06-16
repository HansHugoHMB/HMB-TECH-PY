import subprocess

if __name__ == "__main__":
    subprocess.run(["proxy", "--hostname", "0.0.0.0", "--port", "8080"])