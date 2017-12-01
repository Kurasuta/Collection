import argparse
import zipfile
import io
import logging
import hashlib
import os
from lib import Git, HashExtractor, Sample, SampleDumper


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        print('[%s] %s' % (record.levelname, record.msg))


parser = argparse.ArgumentParser(description='convert https://github.com/ytisf/theZoo into feed of samples')
parser.add_argument('git', help='directory containing git checkout')
parser.add_argument('target', help='directory for result')
parser.add_argument('--debug', help='enables debug logging', action='store_true')
args = parser.parse_args()

logger = logging.getLogger('KurasutaSampleCollection::TheZoo')
logger.handlers.append(ConsoleHandler())
logger.setLevel(logging.DEBUG if args.debug else logging.WARNING)

extractor = HashExtractor()
dumper = SampleDumper(args.target)

git = Git(args.git)
git.pull()
for root, dir, files in os.walk(os.path.join(args.git, 'malwares', 'Binaries')):
    if len(files) != 4:
        continue

    check_md5 = None
    check_sha256 = None
    check_sha1 = None
    password = None
    zip_content = None
    for file_name in files:
        if file_name.endswith('.md5'):
            content = open(os.path.join(root, file_name), 'r').read()
            extracted = extractor.extract_md5(content)
            if len(extracted) == 1:
                check_md5 = extracted[0]
            elif len(extracted) == 0:
                logger.warning('could not read check_md5 in "%s"' % root)
            else:
                logger.warning('could not read unique check_md5 in "%s"' % root)
        elif file_name.endswith('.sha256'):
            content = open(os.path.join(root, file_name), 'r').read().strip()
            extracted = extractor.extract_sha256(content)
            if len(extracted) == 1:
                check_sha256 = extracted[0]
            elif len(extracted) == 0:
                logger.warning('could not read check_sha256 in "%s"' % root)
            else:
                logger.warning('could not read unique check_sha256 in "%s"' % root)
        elif file_name.endswith('.sha'):
            content = open(os.path.join(root, file_name), 'r').read().strip()
            extracted = extractor.extract_sha1(content)
            if len(extracted) == 1:
                check_sha1 = extracted[0]
            elif len(extracted) == 0:
                logger.warning('could not read check_sha1 in "%s"' % root)
            else:
                logger.warning('could not read unique check_sha1 in "%s"' % root)
        elif file_name.endswith('.pass'):
            password = open(os.path.join(root, file_name), 'rb').read().strip()
        elif file_name.endswith('.zip'):
            zip_content = open(os.path.join(root, file_name), 'rb').read()

    if zip_content is None or password is None:
        continue
    if check_sha256 is None and check_md5 is None and check_sha1 is None:
        logger.warning('No checksum available in "%s"' % root)

    if check_sha256 is not None:
        actual_sha256 = hashlib.sha256(zip_content).hexdigest().lower()
        if check_sha256 != actual_sha256:
            logger.warning('sha256 mismatch in "%s": "%s" != "%s"' % (root, actual_sha256, check_sha256))

    if check_sha1 is not None:
        actual_sha1 = hashlib.sha1(zip_content).hexdigest().lower()
        if check_sha1 != actual_sha1:
            logger.warning('sha1 mismatch in "%s": "%s" != "%s"' % (root, actual_sha1, check_sha1))

    if check_md5 is not None:
        actual_md5 = hashlib.md5(zip_content).hexdigest().lower()
        if check_md5 != actual_md5:
            logger.warning('md5 mismatch in "%s": "%s" != "%s"' % (root, actual_md5, check_md5))

    if dumper.is_dumped(actual_sha256):
        continue
    logger.debug('Unpacking in "%s"' % root)
    zip_data = io.BytesIO()
    zip_data.write(zip_content)
    z = zipfile.ZipFile(zip_data)

    try:
        samples = [Sample(z.read(name, pwd=password), [os.path.basename(root)], [name]) for name in z.namelist()]
        logger.debug('Dumping %i samples' % len(samples))
        for sample in samples:
            logger.debug('Dumping sample with hash "%s"' % sample.sha256)
            dumper.dump(sample)
        dumper.mark_dumped(actual_sha256)
    except RuntimeError as e:
        logger.warning('Exception during extraction in "%s" with password "%s": %s' % (root, password, e))
