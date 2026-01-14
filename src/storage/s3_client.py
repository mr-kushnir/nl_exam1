"""
S3 Client for Yandex Object Storage
"""

import os
import json
from typing import Optional, BinaryIO
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


class S3Client:
    """Yandex Object Storage client (S3-compatible)"""
    
    ENDPOINT = 'https://storage.yandexcloud.net'
    REGION = 'ru-central1'
    
    def __init__(self, bucket: str = None):
        self.bucket = bucket or os.getenv('S3_BUCKET', '')
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            if not HAS_BOTO:
                raise RuntimeError("boto3 not installed. Run: pip install boto3")
            
            self._client = boto3.client(
                's3',
                endpoint_url=self.ENDPOINT,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.REGION,
                config=Config(signature_version='s3v4')
            )
        return self._client
    
    def upload_file(self, file_path: str, object_name: str = None) -> str:
        """Upload file to S3"""
        if object_name is None:
            object_name = Path(file_path).name
        
        self.client.upload_file(file_path, self.bucket, object_name)
        return self.get_url(object_name)
    
    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """Upload bytes to S3"""
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=data,
            ContentType=content_type
        )
        return self.get_url(object_name)
    
    def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """Upload file object to S3"""
        self.client.upload_fileobj(file_obj, self.bucket, object_name)
        return self.get_url(object_name)
    
    def download_file(self, object_name: str, file_path: str) -> str:
        """Download file from S3"""
        self.client.download_file(self.bucket, object_name, file_path)
        return file_path
    
    def download_bytes(self, object_name: str) -> bytes:
        """Download file as bytes"""
        response = self.client.get_object(Bucket=self.bucket, Key=object_name)
        return response['Body'].read()
    
    def delete(self, object_name: str) -> bool:
        """Delete object from S3"""
        self.client.delete_object(Bucket=self.bucket, Key=object_name)
        return True
    
    def exists(self, object_name: str) -> bool:
        """Check if object exists"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except:
            return False
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> list:
        """List objects in bucket"""
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        objects = []
        for obj in response.get('Contents', []):
            objects.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'modified': obj['LastModified'].isoformat()
            })
        return objects
    
    def get_url(self, object_name: str) -> str:
        """Get public URL for object"""
        return f"{self.ENDPOINT}/{self.bucket}/{object_name}"
    
    def get_presigned_url(self, object_name: str, expiration: int = 3600, method: str = 'get_object') -> str:
        """Get presigned URL for temporary access"""
        return self.client.generate_presigned_url(
            method,
            Params={'Bucket': self.bucket, 'Key': object_name},
            ExpiresIn=expiration
        )
    
    def get_presigned_upload_url(self, object_name: str, expiration: int = 3600, content_type: str = None) -> dict:
        """Get presigned URL for upload"""
        params = {'Bucket': self.bucket, 'Key': object_name}
        if content_type:
            params['ContentType'] = content_type
        
        return {
            'url': self.client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=expiration
            ),
            'fields': {}
        }


# Local filesystem fallback
class LocalStorage:
    """Local filesystem storage for development"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv('LOCAL_STORAGE_PATH', './storage'))
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _path(self, object_name: str) -> Path:
        return self.base_path / object_name
    
    def upload_file(self, file_path: str, object_name: str = None) -> str:
        if object_name is None:
            object_name = Path(file_path).name
        
        import shutil
        dest = self._path(object_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest)
        return str(dest)
    
    def upload_bytes(self, data: bytes, object_name: str, content_type: str = None) -> str:
        dest = self._path(object_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return str(dest)
    
    def download_file(self, object_name: str, file_path: str) -> str:
        import shutil
        shutil.copy2(self._path(object_name), file_path)
        return file_path
    
    def download_bytes(self, object_name: str) -> bytes:
        return self._path(object_name).read_bytes()
    
    def delete(self, object_name: str) -> bool:
        path = self._path(object_name)
        if path.exists():
            path.unlink()
        return True
    
    def exists(self, object_name: str) -> bool:
        return self._path(object_name).exists()
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> list:
        objects = []
        for path in self.base_path.rglob('*'):
            if path.is_file():
                rel_path = path.relative_to(self.base_path)
                if str(rel_path).startswith(prefix):
                    objects.append({
                        'key': str(rel_path),
                        'size': path.stat().st_size,
                        'modified': path.stat().st_mtime
                    })
        return objects[:max_keys]
    
    def get_url(self, object_name: str) -> str:
        return f"file://{self._path(object_name).absolute()}"
    
    def get_presigned_url(self, object_name: str, expiration: int = 3600, method: str = 'get') -> str:
        return self.get_url(object_name)


def get_storage(bucket: str = None):
    """Get storage client (S3 or local fallback)"""
    if os.getenv('AWS_ACCESS_KEY_ID') and HAS_BOTO:
        return S3Client(bucket)
    else:
        return LocalStorage()


# CLI
if __name__ == "__main__":
    import sys
    
    storage = get_storage()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python s3_client.py upload <file_path> [object_name]")
        print("  python s3_client.py download <object_name> <file_path>")
        print("  python s3_client.py list [prefix]")
        print("  python s3_client.py delete <object_name>")
        print("  python s3_client.py url <object_name>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "upload":
        file_path = sys.argv[2]
        object_name = sys.argv[3] if len(sys.argv) > 3 else None
        url = storage.upload_file(file_path, object_name)
        print(f"Uploaded: {url}")
    
    elif cmd == "download":
        object_name = sys.argv[2]
        file_path = sys.argv[3]
        storage.download_file(object_name, file_path)
        print(f"Downloaded: {file_path}")
    
    elif cmd == "list":
        prefix = sys.argv[2] if len(sys.argv) > 2 else ''
        objects = storage.list_objects(prefix)
        print(json.dumps(objects, indent=2))
    
    elif cmd == "delete":
        object_name = sys.argv[2]
        storage.delete(object_name)
        print("Deleted")
    
    elif cmd == "url":
        object_name = sys.argv[2]
        print(storage.get_url(object_name))
