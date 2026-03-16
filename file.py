"""
This script handles everything related to Files and AWS IO for the Verkiezingswinnaar project.
"""

import gzip
import json
import os
import shutil
import time

import boto3

class File:
    filename_json: str
    filename_jsonl: str
    filename_gz: str

    def __init__(self, filename):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs("debugging/", exist_ok=True)
        self.filename_json = "debugging/" + filename + " " + timestamp + ".json"
        self.filename_jsonl = filename + ".jsonl"
        self.filename_gz = self.filename_jsonl + ".gz"

    def dump_to_json(self, data: dict) -> None:
        with open(self.filename_json, "a") as f:
            json.dump(data, f, indent=2)

    def dump_to_jsonl(self, data: dict) -> None:
        with open(self.filename_jsonl, "a") as f:
            json.dump(data, f, separators=(',', ':'))
            f.write("\n")

    def compress_jsonl_to_gz(self) -> None:
        with open(self.filename_jsonl, "rb") as f_in:
            with gzip.open(self.filename_gz, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out) # type: ignore

    def upload_to_s3(self, filename: str) -> None:
        s3 = boto3.client("s3", region_name="eu-north-1")
        s3.upload_file(
            Bucket="verkiezingswinnaar",
            Filename=filename,
            Key=filename,
            ExtraArgs={"ACL": "public-read",
                       "CacheControl": "no-cache"}
        )
        print(filename + " uploaded")

    def upload_json_to_s3(self) -> None:
        self.upload_to_s3(self.filename_json)

    def upload_gz_to_s3(self) -> None:
        self.upload_to_s3(self.filename_gz)

    def delete_jsonl(self):
        os.remove(self.filename_jsonl)
