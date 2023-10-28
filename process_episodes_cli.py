import logging
import os
from argparse import ArgumentParser

from utils.mongo_db_utils import get_chunked_transcriptions_coll
from utils.rss_utils import get_rss_episodes
from utils.spotify_utils import get_spotify_episode_info
from utils.embedding_utils import SentenceEmbedder
from utils.whisper_utils import Transcriber


CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
AUDIO_TRANSCRIPTION_MODEL = "openai/whisper-small.en"
EMBEDDING_MODEL = "all-mpnet-base-v2"

def main(args):

    logger = logging.getLogger('main-logger')
    logger.setLevel(args.log_level.upper())
    console_handler = logging.StreamHandler()
    console_handler.setLevel(args.log_level.upper())
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.info("Logger instantiated")

    all_rss_episodes = get_rss_episodes(args.rss_url)
    sorted_rss_episodes = sorted(
        all_rss_episodes, key=lambda x: x["date_str"] + x["title"]
    )
    logger.info(f"Got {len(all_rss_episodes)} RSS episodes")

    _, spotify_episode_mapping = get_spotify_episode_info(
        CLIENT_ID, CLIENT_SECRET, args.spotify_id
    )
    logger.info(f"Got {len(spotify_episode_mapping.keys())} Spotify episodes")

    ct_coll = get_chunked_transcriptions_coll(args.db_name, args.coll_name)

    cursor = ct_coll.aggregate(
        [
            {
                "$group": {
                    "_id": "all",
                    "episodes": {
                        "$addToSet": "$episode_info.name",
                    },
                    "max_published": {
                        "$max": "$episode_info.published_date",
                    },
                }
            }
        ]
    )
    ct_stats = list(cursor)
    max_published = "0000-00-00"
    coll_episodes = []
    if ct_stats:
        max_published = ct_stats[0]["max_published"]
        coll_episodes = ct_stats[0]["episodes"]
    logger.info(
        f"Got collection stats: {len(coll_episodes)} episodes with max published {max_published}"
    )

    transcriber = Transcriber(AUDIO_TRANSCRIPTION_MODEL)
    logger.info("Transcriber instantiated.")
    embedder = SentenceEmbedder(EMBEDDING_MODEL)
    logger.info("Text embedder instantiated.")
    transcribed_count = 0
    for episode in sorted_rss_episodes:
        if transcribed_count >= args.max_n:
            logger.info(f"{transcribed_count} transcribed, stopping.")
            break
        if episode["title"] in coll_episodes and episode["date_str"] <= max_published:
            logger.info(f"Skipping {episode['title']}.")
            continue

        transcribed_doc = transcriber.transcribe_file_from_url(episode["mp3_url"])
        logger.info(f"Transcribed {episode['title']}.")

        processed_ep_docs = embedder.get_paragraphs_with_embeddings(
            transcribed_doc,
            episode_info={
                "name": episode["title"],
                "published_date": episode["date_str"],
                "spotify_id": spotify_episode_mapping.get(
                    (episode["title"], episode["date_str"])
                ),
            },
            other_doc_info={
                "embedding_model": EMBEDDING_MODEL,
                "transcription_model": AUDIO_TRANSCRIPTION_MODEL,
            }
        )
        logger.info(f"Processed {episode['title']}.")
        
        logger.info("Inserting into collection.")
        insertion_result = ct_coll.insert_many(processed_ep_docs)
        logger.info(insertion_result)

        transcribed_count += 1
        logger.info(f"{transcribed_count} added to database so far.")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--rss-url",
        default="https://podcast.global.com/show/5234547/episodes/feed",
    )
    parser.add_argument("--spotify-id", default="44u5271Rsz60P8xtn0aWDd")
    parser.add_argument("--db-name", default="podcast_transcriptions")
    parser.add_argument("--coll-name", default="beans")
    parser.add_argument("--max-n", default=1, type=int)
    parser.add_argument("--log-level", default="warning")

    args = parser.parse_args()

    main(args)
