"""
Handle pubmed historical data.

Parse the pubmed baseline article sets and generate jsonl PubMedArticles to be
used by classifier.

The script expects path to folder containing pubmed baseline .xml.gz files,
the path to output directory where generated files should be stored, and
number of concurrent processes to be used [1, 16].
"""
import logging
import sys
import os
import gzip
import shutil
from datetime import datetime
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
from pubmed import PubMedArticle, ArticleSetParser


def is_xml_article_set(filename: str) -> bool:
    """
    Check if input file is pubmed xml compressed archive from name.

    Arguments:
        filename {str} -- the name of the file

    Returns:
        bool -- true if file is compressed pubmed article set
    """
    if filename.endswith(".xml.gz"):
        return True
    return False


def decompress_article_set(file_path: str, output_file: str):
    """
    Unzip articles sets and create xml file.

    Arguments:
        file_path {str} -- absolute path to article set gz file
        output_file {str} -- absolute path to created decompressed file
    """
    with gzip.open(file_path, "rb") as f_in:
        with open(output_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def parse_pubmed_article_set(in_path: str, out_path: str):
    """
    Convert xml to json articles.

    Crawls through all files in a directory and create equivalent parsed jsonl file
    in output_path

    Arguments:
        in_path {str} -- absolute path to directory containing compressed article sets
        out_path {str} -- absolute path to desired directory to save output jsonl files
    """
    filename = os.path.basename(in_path)
    if not is_xml_article_set(filename):
        return
    xml_file = in_path.replace(".gz", "")
    if not os.path.exists(xml_file):
        logging.info("Extracting %s to %s", in_path, xml_file)
        decompress_article_set(in_path, xml_file)

    logging.info("Parsing %s", xml_file)
    article_list: PubMedArticle = ArticleSetParser.extract_articles(xml_file)

    # Done with xml - delete to free up space
    os.remove(xml_file)

    output_file = os.path.join(out_path, filename.replace(".xml.gz", ".jsonl"))
    logging.info("Generating %s", output_file)
    ArticleSetParser.articles_to_jsonl(article_list, output_file)

    logging.info("Compressing file: %s", output_file)
    with open(output_file, "rb") as jsonl_data:
        data_jsonl = jsonl_data.read()
    compressed_data = gzip.compress(data_jsonl)
    output_file_compressed = output_file + ".gz"
    with open(output_file_compressed, "wb") as out_compressed:
        out_compressed.write(compressed_data)

    # Done with parsed file - delete to free up space
    os.remove(output_file)

    logging.info(
        "PID: %s. File Processed: %s. Articles Processed %s",
        os.getpid(),
        output_file,
        len(article_list),
    )
    return


def concurrent_execution(data_in_dir, data_out_dir, max_workers):
    """Concurrent execution manager. Spawns workers to parse files."""
    start_time = datetime.now()
    xml_files: [str] = []
    for filename in os.listdir(data_in_dir):
        if is_xml_article_set(filename):
            xml_files.append(os.path.join(data_in_dir, filename))

    logging.info("Found %s PubMed article sets", len(xml_files))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(parse_pubmed_article_set, xml_files, repeat(data_out_dir))

    end_time = datetime.now()
    total_time = end_time - start_time
    logging.info(
        "Concurrent Process %s Execution: %s files, in %s",
        max_workers,
        len(xml_files),
        total_time,
    )


if __name__ == "__main__":
    ERROR_MSG = "Command line arguments expected: <path to data dir>, \
        <path to output dir>, <number of parallel processes (2-16)>"

    if not sys.argv or len(sys.argv) < 4:
        raise ValueError(ERROR_MSG)

    # check command line argument for input directory
    if os.path.isdir(sys.argv[1]):
        DATA_IN_DIR = sys.argv[1]
    else:
        raise ValueError("Input data directory is not valid. " + ERROR_MSG)

    # check command line argument for output directory
    if os.path.isdir(sys.argv[2]):
        DATA_OUT_DIR = sys.argv[2]
    else:
        raise ValueError("Output data directory is not valid. " + ERROR_MSG)

    # check argument for number of parallel processes
    try:
        MAX_WORKERS = int(sys.argv[3])
        if MAX_WORKERS < 1 or MAX_WORKERS > 16:
            logging.error(
                "Invalid number of workers requested - Setting number of \
                workers to 1"
            )
            MAX_WORKERS = 1
    except TypeError:
        logging.error(
            "Max number of processes should be a valid integer. %s", ERROR_MSG
        )

    concurrent_execution(DATA_IN_DIR, DATA_OUT_DIR, MAX_WORKERS)
