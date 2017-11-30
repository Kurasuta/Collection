import hashlib
import os
import json
import subprocess
import re


class Git(object):
    def __init__(self, repository_path):
        self.repository_path = repository_path
        assert os.path.exists(os.path.join(repository_path, '.git'))

    def _git(self, *args):
        result, error = subprocess.Popen(
            ['git'] + list(args),
            cwd=self.repository_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        if error:
            raise Exception(error)
        return result

    def pull(self):
        return self._git('pull')


class HashExtractor(object):
    def __init__(self):
        self.r_md5 = re.compile('([a-fA-F\d]{32})', re.IGNORECASE)
        self.r_sha256 = re.compile('([a-fA-F\d]{64})', re.IGNORECASE)
        self.r_sha1 = re.compile('([a-fA-F\d]{40})', re.IGNORECASE)

    def extract_md5(self, data):
        return self.r_md5.findall(data)

    def extract_sha1(self, data):
        return self.r_sha1.findall(data)

    def extract_sha256(self, data):
        return self.r_sha256.findall(data)


class Sample(object):
    def __init__(self, payload, tags, file_names, source_id=None):
        self.payload = payload  # type: bytes
        self.tags = tags  # type: list(str)
        self.file_names = file_names  # type: list(str)
        self.source_id = source_id  # type: None|str

    @property
    def sha256(self):
        return hashlib.sha256(self.payload).hexdigest()

    def __repr__(self):
        return '<Sample %s %s:%s>' % (self.sha256, self.file_names, self.tags)

    def to_json(self):
        ret = {'tags': self.tags, 'file_names': self.file_names}
        if self.source_id is not None:
            ret['source_id'] = self.source_id
        return json.dumps(ret)


class SampleDumper(object):
    def __init__(self, target_directory):
        self.target_directory = target_directory  # type: str

    def dump(self, sample):
        target_path = os.path.join(self.target_directory, sample.sha256)
        if os.path.exists(target_path):
            return

        # write metadata to json file
        with open(target_path + '.json', 'w') as fp:
            fp.write(sample.to_json())
            fp.close()

        with open(target_path, 'wb') as fp:
            fp.write(sample.payload)
            fp.close()
