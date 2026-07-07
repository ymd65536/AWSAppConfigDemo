FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/var/task

RUN python3 - <<'PY'
import os
import shutil
import tarfile
import urllib.request

url = 'https://github.com/awslabs/aws-lambda-web-adapter/releases/download/v0.8.4/aws-lambda-adapter-0.8.4-linux-amd64.tar.gz'
archive_path = '/tmp/aws-lambda-adapter.tar.gz'
urllib.request.urlretrieve(url, archive_path)

with tarfile.open(archive_path, 'r:gz') as archive:
    archive.extractall('/tmp/aws-lambda-adapter')

for root, _, files in os.walk('/tmp/aws-lambda-adapter'):
    for name in files:
        if name == 'aws-lambda-adapter':
            os.makedirs('/opt/extensions', exist_ok=True)
            shutil.copy(os.path.join(root, name), '/opt/extensions/lambda-adapter')
            break
    else:
        continue
    break

os.remove(archive_path)
shutil.rmtree('/tmp/aws-lambda-adapter', ignore_errors=True)
PY

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app /var/task/app
COPY . /var/task

CMD ["uvicorn", "app.step4_bedrock:app", "--host", "0.0.0.0", "--port", "8080"]
